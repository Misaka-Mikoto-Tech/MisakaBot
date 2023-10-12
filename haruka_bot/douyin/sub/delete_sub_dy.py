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

delete_sub_dy = on_command("取关抖音", aliases={"抖音取关"}, rule=to_me(), priority=5, block=True)
delete_sub_dy.__doc__ = """取关抖音 用户名"""

delete_sub_dy.handle()(permission_check)

@delete_sub_dy.handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, arg_msg: Message = CommandArg()
):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)

@delete_sub_dy.got("arg", "请发送抖音用户名")
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, arg: str = ArgPlainText("arg")
):
    vive_texts = arg.strip().split(' ')

    user_name = vive_texts[0].strip()
    if user_name.startswith('MS4wLj') and len(user_name) > 50: # 用户输入了一个 sec_uid
        sec_uid = user_name
    else:
        user = await db.get_user_dy(name=user_name) # 从数据库中查找用户名，因为用户可以改名，可能目前已经不是这个名字了
        if not user:
            return await delete_sub_dy.send(MessageSegment.at(event.user_id) + " 未找到该 UP，请输入正确的UP 名、sec_uid")
        sec_uid = user.sec_uid
    
    result = await db.delete_sub_dy(
        sec_uid=sec_uid,
        group_id=event.group_id,
        bot_id=int(bot.self_id)
    )

    if result:
        await delete_sub_dy.finish(f"已取关 {user_name}")
    await delete_sub_dy.finish(f"{user_name}未关注")