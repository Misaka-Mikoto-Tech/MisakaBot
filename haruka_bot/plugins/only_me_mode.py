from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.exception import IgnoredException
# from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.message import run_preprocessor, event_preprocessor
from nonebot.log import logger

only_me_mode: bool = False

only_me_on = on_command("只听我的", aliases={"凛雅,只听我的", "凛雅，只听我的"}, permission=SUPERUSER, priority=1, block=True)
only_me_off = on_command("听大家的", aliases={"凛雅,听大家的", "凛雅，听大家的"}, permission=SUPERUSER, priority=1, block=True)

@only_me_on.handle()
@only_me_off.handle()
async def on_only_me_on(bot: Bot, event: MessageEvent, matcher: Matcher):
    """指令处理函数"""
    global only_me_mode
    msg = event.get_plaintext().strip()
    if '只听我的' in msg:
        only_me_mode = True
        await matcher.finish('好的，现在只听我的')
    else:
        only_me_mode = False
        await matcher.finish('好的，现在听大家的')

@run_preprocessor
async def check_only_me_mode(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    """独占模式Matcher过滤函数"""
    if bot.self_id == str(event.sender.user_id):
        return
    elif only_me_mode:
        # await matcher.finish(f'达咩')
        raise IgnoredException("独占模式，取消执行Matcher")
    
@event_preprocessor
async def on_event_pre_processor(bot: Bot, event: GroupMessageEvent):
    """事件过滤函数"""
    # if not event.group_id in [123456, 789]: # 白名单群号列表，可以填入配置文件
    #     raise IgnoredException("群号不在白名单中，取消派发")