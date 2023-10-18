from typing import List
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, Reply
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.message import Message
from nonebot.params import CommandArg
from nonebot.internal.matcher import Matcher

from ..utils import on_command, to_me, text_to_img
from ..version import __version__
from .. import config

debug = on_command("debug", permission=SUPERUSER, priority=2, block=True)

@debug.handle()
async def _(event: GroupMessageEvent, bot:Bot, matcher: Matcher, arg: Message = CommandArg()):
    """输出回复的原始消息内容"""
    if event.reply:
        if arg.extract_plain_text().strip() == 'echo':
            await matcher.finish(event.reply.message)
        else:
            await matcher.finish('{' + str(event.reply) +'}')
