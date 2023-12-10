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
from ... import config
from ..utils_weibo import get_userinfo, get_user_dynamics, search_weibo_user, set_uid_arg_by_q

add_sub_weibo = on_command("关注微博", aliases={"微博关注", "微博订阅"}, rule=to_me(), priority=5, block=True)
add_sub_weibo.__doc__ = """关注微博 uid/用户名"""

add_sub_weibo.handle()(permission_check)

@add_sub_weibo.handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, arg: Message = CommandArg()
):
    arg_text =arg.extract_plain_text().strip()
    if not arg_text:
        await matcher.finish('未获取到关注uid/用户名')
    
    await set_uid_arg_by_q(matcher=matcher, q=arg_text)

@add_sub_weibo.got("uid", "请发送微博uid")
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot
    , uid: str = ArgPlainText("uid")
):
    if not uid.isdigit():
        await matcher.finish("请输入纯数字uid")

    try:
        user_info = await get_userinfo(uid=int(uid))
    except Exception as e:
        await matcher.finish(f"获取微博用户出错，{e.args}")

    result_exists = await db.get_sub_weibo(group_id=event.group_id,
        bot_id=int(bot.self_id),
        uid=uid)
    
    if result_exists:
        await db.update_sub_weibo(uid=uid,
                                  name=user_info.user_name,
                                  group_id=event.group_id,
                                  bot_id=int(bot.self_id),
                                  )

        await add_sub_weibo.finish(f"已更新微博用户 {user_info.user_name}({uid})")
    else:
        result = await db.add_sub_weibo(uid=uid,
                                        name=user_info.user_name,
                                        group_id=event.group_id,
                                        bot_id=int(bot.self_id),
                                        containerid=user_info.containerid
                                        )
        if result:
            await add_sub_weibo.finish(f"已关注微博用户 {user_info.user_name}({uid})")
        await add_sub_weibo.finish(f" {user_info.user_name}({uid}) 已经关注了")
