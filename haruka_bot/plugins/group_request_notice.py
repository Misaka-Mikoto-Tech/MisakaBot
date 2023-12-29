from typing import Union

from nonebot import on_notice
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11 import GroupRequestEvent
from nonebot.log import logger

group_request_notice = on_notice(priority=5)

@group_request_notice.handle()
async def _(event: GroupRequestEvent, bot: Bot, matcher: Matcher):
    """加群申请处理函数"""
    request_msg = f"bot:{bot.self_id}: {event.user_id} 申请加群 {event.group_id}, 加群信息:{event}"
    user_info = await bot.get_stranger_info(user_id=event.user_id)
    
    logger.info(request_msg)
    logger.info(user_info)

    await matcher.send(f"有人申请加群，申请信息：\n{request_msg}")
    await matcher.send(f"申请人信息：\n{user_info}")