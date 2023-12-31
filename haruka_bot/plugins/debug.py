import time
from typing import List
from httpx import AsyncClient, TransportError
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent, Reply, PrivateMessageEvent
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.adapters.onebot.v11.message import Message
from nonebot.adapters.onebot.v11.adapter import Adapter
from nonebot.params import CommandArg
from nonebot.internal.matcher import Matcher

from ..utils import on_command, to_me, text_to_img, can_at_all
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
            await matcher.finish(f"{nickname}\n{nickname.encode('unicode_escape')}" if nickname else '获取昵称失败')
        else:
            await matcher.finish('{' + str(event.reply) +'}')
    else:
        if arg == 'time': # 回复时间
            now = time.localtime(time.time())
            await matcher.finish(time.strftime("%Y-%m-%d %H:%M:%S", now))
        elif arg.startswith('ping'): # ping 指定地址
            (_, url) = arg.split(' ')
            if not url:
                await matcher.finish('获取地址失败')
            await matcher.finish(await _ping(url=url))
        elif arg.startswith('get_msg'): # 获取指定 message_id 的消息
            await _get_msg(bot, matcher, arg)
        elif arg.startswith('reply'): # 回复指定 message_id 的消息
            await _reply_msg(bot, matcher, arg)
        else:
            await matcher.finish(await debug_help_menu())

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

async def _bili_live_info(bot_id:int, group_id:int):
    """打印当前群组订阅的直播up信息"""

async def _dy_live_info(bot_id:int, group_id:int):
    """打印当前群组订阅的直播up信息"""

async def _get_msg(bot:Bot, matcher: Matcher, arg: str):
    """获取指定 message_id 的消息"""
    _, msg_id = arg.split(' ')
    if not msg_id.isdigit():
        await matcher.finish('未获取到数字格式的 message_id')
    
    try:
        msg_data = await bot.get_msg(message_id=int(msg_id))
        msg_data['self_id'] = int(bot.self_id)
        msg_data['font'] = 0
    except Exception as e:
        await matcher.finish(f'获取消息 {msg_id} 失败:{e.args}')
    
    msg = Adapter.json_to_event(msg_data)
    if not msg:
        await matcher.finish(f'转换消息失败 {msg_id}')

    # 目前只处理 GroupMessageEvent, PrivateMessageEvent
    if isinstance(msg, GroupMessageEvent):
        # 生成转发消息
        msg.group_id
    
async def _reply_msg(bot:Bot, matcher: Matcher, arg: str):
    """回复指定 message_id 的消息"""
    try:
        _, group_id, reply_id, at_id, text = arg.split(' ', 4)
    except Exception as e:
        await matcher.finish(f'参数解析失败，格式为: reply group_id reply_id at_id text')

    msg = MessageSegment.reply(int(reply_id))
    if at_id != '0':
        msg += MessageSegment.at(at_id) + ' '
    msg += text

    # 在指定消息群进行回复（不通过 get_msg 获取原始消息是因为原始消息可能已被撤回）
    await bot.send_group_msg(group_id=int(group_id), message=msg)

async def debug_help_menu()->MessageSegment:
    """debug的帮助菜单"""
    msg = "debug 指令列表\n"
    msg += "# 引用消息时\n"
    msg += "  '': 无参数，发送被引用消息的原始字符串\n"
    msg += "  echo: 发送被引用的消息\n"
    msg += "  nickname: 发送被引用消息的用户nickname\n"
    
    msg += "# 没有引用消息时\n"
    msg += "  time: 发送bot时间\n"
    msg += "  ping: ping指定地址\n"
    msg += "  get_msg: 获取指定消息: id\n"
    msg += "  reply: 回复指定消息: id at text\n"

    message = MessageSegment.image(await text_to_img(msg, width=425))
    return message
