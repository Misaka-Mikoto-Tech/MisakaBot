import re
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
from ..utils_dy import get_user_dynamics, get_sec_user_id, get_aweme_short_url, create_aweme_msg, get_room_id_and_sec_uid_from_live_url
from ... import config

add_sub_dy = on_command("抖音at", rule=to_me(), priority=5, block=True)
add_sub_dy.__doc__ = """抖音at 用户名 开/关"""

add_sub_dy.handle()(permission_check)

@add_sub_dy.handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, arg: Message = CommandArg()
):
    if arg.extract_plain_text().strip():
        matcher.set_arg("args", arg)

@add_sub_dy.got("args", "请发送参数")
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot
    , args: str = ArgPlainText("args")
):
    user_name, switch = args.strip().split(' ')
    if not switch:
        await matcher.finish('未发送开关参数')

    user_info = await db.get_sub_dy(group_id=event.group_id,
        bot_id=int(bot.self_id),
        name=user_name,
        )

    if not user_info:
        await matcher.finish(f'未找到订阅用户 {user_name}')
    
    switch = True if switch == '开' else False
    await db.set_sub_dy(
        "at",
        switch,
        group_id=event.group_id,
        bot_id=int(bot.self_id),
        name=user_name,
    )
    await matcher.finish(f'已 {"开启" if switch else "关闭"} 抖音用户 {user_name} 的直播at全体')