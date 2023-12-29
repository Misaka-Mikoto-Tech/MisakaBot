from typing import Union

from nonebot import on_request
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11 import GroupRequestEvent
from nonebot.log import logger

group_request = on_request(priority=5)

@group_request.handle()
async def _(event: GroupRequestEvent, bot: Bot, matcher: Matcher):
    """加群申请处理函数"""
    msg: Message = MessageSegment.text("有一个加群通知，管理员快去看看吧~\n")
    msg += MessageSegment.image(f'https://q1.qlogo.cn/g?b=qq&s=0&nk={event.user_id}')
    msg += f'\nQQ号：{event.user_id}\n昵称：{event.dict()["nickname"]}\n{event.comment}'

    await matcher.send(msg)