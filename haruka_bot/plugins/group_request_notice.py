from typing import Dict, Optional, Union

from nonebot import on_request, on_command
from nonebot.matcher import Matcher
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import ArgPlainText, CommandArg
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11 import GroupRequestEvent
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.log import logger

# _last_request: Dict[int, GroupRequestEvent] = {} # TODO 考虑每个群存储多个请求

group_request = on_request(priority=5)

@group_request.handle()
async def _(event: GroupRequestEvent, bot: Bot, matcher: Matcher):
    """加群申请处理函数"""
    # global _last_request
    # _last_request[event.group_id] = event

    # ob标准的GroupRequestEvent没有nickname字段，需要单独获取(实际icqq是有此字段的, 但shamrock没有)
    user_info = await bot.get_stranger_info(user_id=event.user_id)

    msg: Message = Message(MessageSegment.text("有一个加群通知，管理员快去看看吧~\n"))
    msg += MessageSegment.image(f'https://q1.qlogo.cn/g?b=qq&s=0&nk={event.user_id}')
    msg += f'\nQQ号：{event.user_id}\n昵称：{user_info["nickname"]}\n{event.comment}'

    await matcher.send(msg)

# group_request_approve = on_command("同意", aliases={"拒绝"}, priority=5, rule=to_me(), permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
# @group_request_approve.handle()
# async def _(event:GroupMessageEvent, bot: Bot, matcher: Matcher):
#     """同意/拒绝加群申请"""
#     global _last_request

#     last_req = _last_request.get(event.group_id)
#     if not last_req:
#         await matcher.finish("没有未处理的加群申请")

#     action = event.message.extract_plain_text().strip()
#     try:
#         if action == '同意':
#             await last_req.approve(bot=bot)
#             await matcher.send('已同意')
#         else:
#             await last_req.reject(bot=bot, reason='管理员拒绝')
#             await matcher.send('已拒绝')
#     finally:
#         del _last_request[event.group_id]