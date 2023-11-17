from bilireq.exceptions import ResponseCodeError
from bilireq.user import get_user_info
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.params import ArgPlainText, CommandArg
from nonebot.internal.matcher import Matcher, current_event
from nonebot_plugin_guild_patch import GuildMessageEvent

from ...database import DB as db
from ...utils import (
    PROXIES,
    get_type_id,
    handle_uid,
    on_command,
    permission_check,
    to_me,
    uid_check,
)
from ...utils.uid_extract import uid_extract
from ...bili_auth import bili_auth

add_sub = on_command("关注", aliases={"添加主播"}, rule=to_me(), priority=5, block=True)
add_sub.__doc__ = """关注 用户名"""

add_sub.handle()(permission_check)

@add_sub.handle()
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg_msg: Message = CommandArg()
):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("user_name", arg_msg)

@add_sub.got("user_name", "请发送UP名称")
async def _(event: MessageEvent, user_name: str = ArgPlainText("user_name")):
    """根据 用户名 订阅 UP 主"""
    user_name = user_name.strip()
    if user_name.isdigit(): # 如果发送的是 uid, 则去获取用户名
        uid = int(user_name)
        user = await db.get_user(uid=uid)
        user_name = user and user.name or ''
        if not user_name:
            try:
                user_name = (await get_user_info(uid, proxies=PROXIES, auth=bili_auth.auth))["name"]
            except ResponseCodeError as e:
                if e.code == -400 or e.code == -404:
                    await add_sub.finish("UID不存在，注意UID不是房间号")
                elif e.code == -412:
                    await add_sub.finish("操作过于频繁IP暂时被风控，请半小时后再尝试")
                else:
                    await add_sub.finish(
                        f"未知错误，请联系开发者反馈，错误内容：\n\
                                        {str(e)}"
                    )
    else: # 发送的是用户名，则去获取 uid
        if not (uid := await uid_extract(user_name)):
            return await add_sub.send(MessageSegment.at(event.user_id) + " 未找到该 UP，请输入正确的UP 名、UP UID或 UP 首页链接")
    
    if isinstance(uid, list):
        return await add_sub.send(MessageSegment.at(event.user_id) + f" 未找到{user_name}, 你是否想要找:\n" + '\n'.join([item['uname'] for item in uid[:10] ]))
    elif int(uid) == 0:
        return await add_sub.send(MessageSegment.at(event.user_id) + " UP 主不存在")

    if isinstance(event, GuildMessageEvent):
        await db.add_guild(
            guild_id=event.guild_id, channel_id=event.channel_id, admin=True
        )
    result = await db.add_sub(
        uid=uid,
        type=event.message_type,
        type_id=await get_type_id(event),
        bot_id=event.self_id,
        name=user_name,
        # TODO 自定义默认开关
        live=True,
        dynamic=True,
        at=False,
        live_tips=''
    )
    if result:
        await add_sub.finish(f"已关注 {user_name}（{uid}）")
    await add_sub.finish(f"{user_name}（{uid}）已经关注了")
