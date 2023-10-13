import asyncio
import sys
from pathlib import Path
from typing import List, Optional, Union, Tuple

import httpx
import nonebot
from nonebot import on_command as _on_command
from nonebot import require
from nonebot.adapters.onebot.v11 import (
    ActionFailed,
    Bot,
    Message,
    MessageEvent,
    MessageSegment,
    NetworkError,
)
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg, RawCommand
from nonebot.permission import SUPERUSER, Permission
from nonebot.rule import Rule
from nonebot_plugin_guild_patch import ChannelDestroyedNoticeEvent, GuildMessageEvent

from ..cli.handle_message_sent import GroupMessageSentEvent

from .. import config


def get_path(*other):
    """获取数据文件绝对路径"""
    if config.haruka_dir:
        dir_path = Path(config.haruka_dir).resolve()
    else:
        dir_path = Path.cwd().joinpath("data")
        # dir_path = Path.cwd().joinpath('data', 'haruka_bot')
    return str(dir_path.joinpath(*other))

async def text_to_img(text, width=500):
    import nonebot_plugin_htmlrender
    css_path = str(Path(__file__).parent / "text_to_pic.css")
    img = await nonebot_plugin_htmlrender.text_to_pic(text, css_path=css_path, width=width)
    return img

async def handle_uid(
    matcher: Matcher,
    command_arg: Message = CommandArg(),
):
    uid = command_arg.extract_plain_text().strip()
    if uid:
        matcher.set_arg("uid", command_arg)

async def handle_uid_and_live_tips(
    matcher: Matcher,
    command_arg: Message = CommandArg(),
):
    arg = command_arg.extract_plain_text()
    if arg.find(':') == -1:
        arg += ':'
    args = arg.split(':')
    uid = args[0]
    live_tips = ':'.join(args[1:])
    if uid:
        matcher.set_arg("uid", Message(uid.strip()))
    matcher.set_arg("live_tips", Message(live_tips)) # live_tips允许为空白

async def uid_check(
    matcher: Matcher,
    uid: str = ArgPlainText("uid"),
):
    uid = uid.strip()
    if not uid.isdecimal():
        await matcher.finish("UID 必须为纯数字")
    matcher.set_arg("uid", Message(uid))


async def _guild_admin(bot: Bot, event: GuildMessageEvent):
    roles = set(
        role["role_name"]
        for role in (
            await bot.get_guild_member_profile(
                guild_id=event.guild_id, user_id=event.user_id
            )
        )["roles"]
    )
    return bool(roles & set(config.haruka_guild_admin_roles))


GUILD_ADMIN: Permission = Permission(_guild_admin)


async def permission_check(
    matcher:Matcher,
    bot: Bot,
    event: Union[GroupMessageEvent, GroupMessageSentEvent, PrivateMessageEvent, GuildMessageEvent]
):
    """检查推送相关操作是否有权限"""
    bot_id = int(bot.self_id)
    async def check_exclusive_bot():
        if (bot_id in config.exclusive_bots) and (event.sender.user_id != bot_id):
            await bot.send(event, "权限不足，本bot为独占模式，不允许其它用户控制")
            raise FinishedException
        
        if (bot_id in config.super_user_mode_bots) and (not await SUPERUSER(bot, event)):
            await bot.send(event, "权限不足，本bot仅允许超级管理员控制")
            raise FinishedException

    if event.sender.user_id == bot_id:
        # Bot 控制自己时永远有权限
        return
    from ..database import DB as db

    if isinstance(event, PrivateMessageEvent):
        if event.sub_type == "group":  # 不处理群临时会话
            raise FinishedException
        return
    if isinstance(event, GroupMessageEvent):
        await check_exclusive_bot()
        if not await db.get_group_admin(event.group_id, bot.self_id):
            return
        if await (GROUP_ADMIN | GROUP_OWNER | SUPERUSER)(bot, event):
            return
    elif isinstance(event, GuildMessageEvent):
        await check_exclusive_bot()
        if not await db.get_guild_admin(event.guild_id, event.channel_id, bot.self_id):
            return
        if await (GUILD_ADMIN | SUPERUSER)(bot, event):
            return
    await bot.send(event, "权限不足，目前只有管理员才能使用")
    raise FinishedException

async def group_only(
    matcher: Matcher, event: PrivateMessageEvent, command: str = RawCommand()
):
    await matcher.finish(f"只有群里才能{command}")


def to_me():
    if config.haruka_to_me:
        from nonebot.rule import to_me

        return to_me()

    async def _to_me() -> bool:
        return True

    return Rule(_to_me)


async def safe_send(bot_id, send_type, type_id, message, at=False, prefix = None):
    """发送出现错误时, 尝试重新发送, 并捕获异常且不会中断运行"""

    async def _safe_send(bot, send_type, type_id, message):
        if send_type == "guild":
            from ..database import DB as db

            guild = await db.get_guild(id=type_id)
            assert guild
            result = await bot.send_guild_channel_msg(
                guild_id=guild.guild_id,
                channel_id=guild.channel_id,
                message=message,
            )
        else:
            result = await bot.call_api(
                "send_" + send_type + "_msg",
                **{
                    "message": message,
                    "user_id" if send_type == "private" else "group_id": type_id,
                },
            )
        return result

    bots = nonebot.get_bots()
    bot = bots.get(str(bot_id))
    if bot is None:
        logger.error(f"推送失败，Bot（{bot_id}）未连接，尝试使用其他 Bot 推送")
        for bot_id, bot in bots.items():
            if at and (
                send_type == "guild"
                or (await bot.get_group_at_all_remain(group_id=type_id))["can_at_all"]
            ):
                message = MessageSegment.at("all") + message
            if prefix:
                message = prefix + message
            try:
                result = await _safe_send(bot, send_type, type_id, message)
                logger.info(f"尝试使用 Bot（{bot_id}）推送成功")
                return result
            except Exception:
                continue
        logger.error("尝试失败，所有 Bot 均无法推送")
        return

    if at and (
        send_type == "guild"
        or (await bot.get_group_at_all_remain(group_id=type_id))["can_at_all"]
    ):
        message = MessageSegment.at("all") + message

    if prefix:
        message = prefix + message
    try:
        return await _safe_send(bot, send_type, type_id, message)
    except ActionFailed as e:
        msg = str(e.info['msg']) if ('msg' in e.info) else ''
        # if msg == "GROUP_NOT_FOUND":
        #     from ..database import DB as db

        #     await db.delete_sub_list(type="group", type_id=type_id, bot_id=bot_id)
        #     await db.delete_group(group_id=type_id, bot_id=bot_id)
        #     logger.error(f"推送失败，群（{type_id}）不存在，已自动清理群订阅列表")
        # elif msg == "CHANNEL_NOT_FOUND":
        #     from ..database import DB as db

        #     guild = await db.get_guild(id=type_id)
        #     assert guild
        #     await db.delete_sub_list(type="guild", type_id=type_id, bot_id=bot_id)
        #     await db.delete_guild(guild_id=type_id, bot_id=bot_id)
        #     logger.error(f"推送失败，频道（{guild.guild_id}|{guild.channel_id}）不存在，已自动清理频道订阅列表")
        # elif msg == "SEND_MSG_API_ERROR":
        #     url = "https://haruka-bot.sk415.icu/usage/faq.html#机器人不发消息也没反应"
        #     logger.error(f"推送失败，账号可能被风控（{url}），错误信息：{e.info}")
        # else:
        logger.error(f"推送失败，未知错误，错误信息：{e.info}")
    except NetworkError as e:
        logger.error(f"推送失败，请检查网络连接，错误信息：{e.msg}")
    except Exception as e:
        logger.error(f"推送失败，错误信息: {e.args}")


async def get_type_id(event: Union[MessageEvent, ChannelDestroyedNoticeEvent]):
    if isinstance(event, GuildMessageEvent) or isinstance(
        event, ChannelDestroyedNoticeEvent
    ):
        from ..database import DB as db

        return await db.get_guild_type_id(guild_id=event.guild_id, channel_id=event.channel_id, bot_id=event.self_id)
    return event.group_id if isinstance(event, GroupMessageEvent) else event.user_id


def check_proxy():
    """检查代理是否有效"""
    if config.haruka_proxy:
        logger.info("检查代理是否有效")
        try:
            httpx.get(
                "https://icanhazip.com/",
                proxies={"all://": config.haruka_proxy},
                timeout=2,
            )
        except Exception:
            raise RuntimeError("加载失败，代理无法连接，请检查 HARUKA_PROXY 后重试")


def on_startup():
    """安装依赖并检查当前环境是否满足运行条件"""
    if config.fastapi_reload and sys.platform == "win32":
        raise ImportError("加载失败，Windows 必须设置 FASTAPI_RELOAD=false 才能正常运行 HarukaBot")
    try:  # 如果开启 realod 只在第一次运行
        asyncio.get_running_loop()
    except RuntimeError:
        from .browser import check_playwright_env, install

        check_proxy()
        install()
        try:
            asyncio.get_event_loop().run_until_complete(check_playwright_env())
        except Exception as ex:
            logger.error(f'check_playwright_env error:{ex}')
        # 创建数据存储目录
        if not Path(get_path()).is_dir():
            Path(get_path()).mkdir(parents=True)


def on_command(cmd, *args, **kwargs):
    return _on_command(config.haruka_command_prefix + cmd, *args, **kwargs)


PROXIES = {"all://": config.haruka_proxy}

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa

from .browser import get_dynamic_screenshot, get_github_screenshot  # noqa
from .get_dynamic_list import get_user_dynamics
