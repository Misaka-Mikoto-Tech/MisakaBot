import time
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
async def _(event: GroupMessageEvent, bot:Bot, matcher: Matcher, argMsg: Message = CommandArg()):
    """输出回复的原始消息内容"""
    arg = argMsg.extract_plain_text().strip()
    if event.reply:
        if arg == 'echo':
            await matcher.finish(event.reply.message)
        else:
            await matcher.finish('{' + str(event.reply) +'}')
    else:
        if arg == 'time':
            now = time.localtime(time.time())
            await matcher.finish(time.strftime("%Y-%m-%d %H:%M:%S", now))