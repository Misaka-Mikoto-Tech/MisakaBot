from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.plugin import on_keyword
from nonebot.matcher import Matcher
from ..utils import permission_check, to_me
from nonebot.log import logger

on_recall = on_keyword({"撤回消息"}, priority=5, block=True)
on_recall.__doc__ = "撤回消息"

@on_recall.handle()
async def recall_handle(matcher:Matcher, bot: Bot, event: GroupMessageEvent):
    if event.reply:
        await permission_check(matcher, bot, event)
        await bot.delete_msg(message_id=event.reply.message_id)
