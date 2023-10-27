import time
from typing import List
from httpx import AsyncClient, TransportError
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, Reply
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.adapters.onebot.v11.message import Message
from nonebot.params import CommandArg
from nonebot.internal.matcher import Matcher

from ..utils import on_command, to_me, text_to_img
from ..version import __version__
from .. import config

debug = on_command("debug", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=2, block=True)

@debug.handle()
async def _(event: GroupMessageEvent, bot:Bot, matcher: Matcher, argMsg: Message = CommandArg()):
    arg = argMsg.extract_plain_text().strip()
    if event.reply:
        # 根据参数输出回复的原始消息内容
        if arg == 'echo':
            await matcher.finish(event.reply.message)
        elif arg == 'nickname':
            nickname = event.reply.sender.nickname
            user_id = event.reply.sender.user_id
            if (not nickname) and user_id:
                nickname = (await bot.get_group_member_info(group_id=event.group_id, user_id=user_id))['nickname']
            await matcher.finish(nickname or '获取昵称失败')
        else:
            await matcher.finish('{' + str(event.reply) +'}')
    else:
        if arg == 'time':
            now = time.localtime(time.time())
            await matcher.finish(time.strftime("%Y-%m-%d %H:%M:%S", now))
        elif arg.startswith('ping'):
            (_, url) = arg.split(' ')
            if not url:
                await matcher.finish('获取地址失败')
            await matcher.finish(await _ping(url=url))

async def _ping(url: str)->str:
    """使用 http head 模拟ping指定地址"""

    msg = f'ping {url}\n'
    if not url.startswith('http'):
        url = 'http://' + url # 绝大多数网站都支持 http
    # 首先尝试不使用代理的延迟
    try:
        dt = time.time()
        async with AsyncClient() as client:
            await client.head(url=url, timeout=5)
        span = int((time.time() - dt) * 1000)
        msg += f'direct: {span}ms\n'
    except TransportError as e:
        msg += 'direct: timeout\n'
    except Exception as e:
        msg += f'direct: {e.args}'

    # 再测试使用代理的延迟
    try:
        dt = time.time()
        async with AsyncClient(proxies=config.overseas_proxy) as client:
            await client.head(url=url, timeout=5)
        span = int((time.time() - dt) * 1000)
        msg += f'proxy: {span}ms'
    except TransportError as e:
        msg += 'proxy: timeout'
    except Exception as e:
        msg += f'proxy: {e.args}'

    return msg.strip()