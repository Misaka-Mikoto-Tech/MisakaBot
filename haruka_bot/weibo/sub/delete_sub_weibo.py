from datetime import datetime
from typing import List
from loguru import logger
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent
from nonebot.internal.matcher import Matcher, current_event
from nonebot.params import ArgPlainText, CommandArg

from ...database import DB as db
from ...utils import on_command, to_me, permission_check

delete_sub_weibo = on_command("取关微博", aliases={"微博取关"}, rule=to_me(), priority=5, block=True)
delete_sub_weibo.__doc__ = """取关微博 uid/用户名"""

delete_sub_weibo.handle()(permission_check)

@delete_sub_weibo.handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, arg_msg: Message = CommandArg()
):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("uid", arg_msg)

@delete_sub_weibo.got("uid", "请发送微博uid")
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, uid: str = ArgPlainText("uid")
):
    if uid.isdigit():
        user = await db.get_user_weibo(uid=int(uid)) # 从数据库中查找用户信息
    else:
        user = await db.get_user_weibo(name=uid) # 从数据库中查找用户信息
    if not user:
        return await delete_sub_weibo.send(MessageSegment.at(event.user_id) + " 未找到该微博用户")
    
    result = await db.delete_sub_weibo(
        uid=int(uid),
        group_id=event.group_id,
        bot_id=int(bot.self_id)
    )

    if result:
        await delete_sub_weibo.finish(f"已取关 {user.name}({user.uid})")
    await delete_sub_weibo.finish(f"{user.name}未关注")