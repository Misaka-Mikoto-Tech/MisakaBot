from datetime import datetime
from typing import List
from loguru import logger
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent
from nonebot.internal.matcher import Matcher, current_event
from nonebot.params import ArgPlainText, CommandArg

from ...database import DB as db
from ...utils import on_command, to_me, permission_check, text_to_img
from ..utils_dy import get_user_dynamics, get_sec_user_id, get_aweme_short_url, create_aweme_msg
from ... import config

add_sub_dy = on_command("关注抖音", aliases={"抖音关注"}, rule=to_me(), priority=5, block=True)
add_sub_dy.__doc__ = """关注抖音 用户名 [直播间号,可选]"""

add_sub_dy.handle()(permission_check)

@add_sub_dy.handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, arg_msg: Message = CommandArg()
):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)

@add_sub_dy.got("arg", "请发送抖音用户名")
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, arg: str = ArgPlainText("arg")
):
    vive_texts = arg.strip().split(' ')

    user_name = vive_texts[0]
    if not (sec_uid := await get_sec_user_id(user_name=user_name)):
        return await add_sub_dy.send(MessageSegment.at(event.user_id) + " 未找到该抖音用户名")

    if isinstance(sec_uid, list):
        return await add_sub_dy.send(MessageSegment.at(event.user_id) + f" 未找到{user_name}, 你是否想要找:\n" + '\n'.join([item['user_info']['nickname'] for item in sec_uid[:10] ]))
    
    room_id = vive_texts[1] if len(vive_texts) > 1 else 0
    room_str = f"({room_id})" if room_id != 0 else ''

    result_exists = await db.get_sub_dy(group_id=event.group_id,
        bot_id=int(bot.self_id),
        sec_uid=sec_uid)
    
    if result_exists:
        await db.update_sub_dy(name=user_name,
            group_id=event.group_id,
            bot_id=int(bot.self_id),
            sec_uid=sec_uid,
            room_id=room_id)

        await add_sub_dy.finish(f"已更新抖音用户 {user_name}{room_str}")
    else:
        result = await db.add_sub_dy(
            name=user_name,
            group_id=event.group_id,
            bot_id=int(bot.self_id),
            sec_uid=sec_uid,
            room_id=room_id
        )
        if result:
            await add_sub_dy.finish(f"已关注抖音用户 {user_name}{room_str}")
        await add_sub_dy.finish(f"{user_name}{room_str} 已经关注了")