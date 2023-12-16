from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.exception import IgnoredException
# from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.message import run_preprocessor
from nonebot.log import logger

only_me_mode: bool = False

only_me_on = on_command("只听我的", aliases={"凛雅,只听我的", "凛雅，只听我的"}, permission=SUPERUSER, priority=5, block=True)
only_me_off = on_command("听大家的", aliases={"凛雅,听大家的", "凛雅，听大家的"}, permission=SUPERUSER, priority=5, block=True)

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
async def check_only_me_mode(bot: Bot, event: MessageEvent, matcher: Matcher):
    """独占模式Matcher预处理器"""
    if bot.self_id == str(event.sender.user_id):
        return
    elif only_me_mode:
        # await matcher.finish(f'达咩')
        raise IgnoredException("独占模式，取消执行Matcher")
    
