from typing import List, Optional, Tuple

from nonebot.matcher import Matcher
from nonebot_plugin_guild_patch import GUILD_ADMIN, GuildMessageEvent
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11.event import Sender, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER

async def permission_check_chatgpt(matcher:Matcher, event: Event, bot:Bot, cmd:str, type:str = 'cmd') -> Tuple[bool, Optional[str]]:
    """chatgpt相关的操作权限检查"""

    from ...database import DB as db

    bot_id = int(bot.self_id)
    enable_chatgpt:bool = False
    if isinstance(event, GroupMessageEvent):
        grp_event:GroupMessageEvent = event
        enable_chatgpt = await db.get_group_chatgpt(group_id=grp_event.group_id,bot_id=bot.self_id)
    elif isinstance(event, GuildMessageEvent):
        gld_event:GuildMessageEvent = event
        enable_chatgpt = await db.get_guild_chatgpt(guild_id=gld_event.guild_id,channel_id=gld_event.channel_id,bot_id=bot.self_id)

    if not enable_chatgpt:
        return (False, '本群没有开启ChatGPT功能，查询开启指令请输入 帮助')

    if not cmd: # None or ''
        return (True, None)
    
    if not hasattr(event, 'sender'):
        return (True, None)
    else:
        sender:Sender = getattr(event, 'sender')

    if sender.user_id == int(bot.self_id): # bot 自身永远有权限
        return (True, None)

    args:List[str] = cmd.split(' ')
 
    from haruka_bot import config
    def check_exclusive_bot() -> bool:
        return not ((bot_id in config.exclusive_bots) and (sender.user_id != bot_id))
    
    async def check_super_user_mode() -> bool:
        return not ((bot_id in config.super_user_mode_bots) and (not await SUPERUSER(bot, event)))

    has_permission:bool = False
    err_msg = '权限不足，无法完成操作'
    if isinstance(event, PrivateMessageEvent):
        has_permission = False
    if isinstance(event, GroupMessageEvent):
        if not check_exclusive_bot():
            has_permission = False
            err_msg = '本Bot为独占模式，只有本人可以操作'
        elif not await check_super_user_mode():
            has_permission = False
            err_msg = '权限不足，本bot仅允许超级管理员控制'
        elif (await db.get_group_admin(event.group_id, bot.self_id)) or (await (GROUP_ADMIN | GROUP_OWNER | SUPERUSER)(bot, event)):
            has_permission = True
    elif isinstance(event, GuildMessageEvent):
        if not check_exclusive_bot():
            has_permission =  False
            err_msg = '本Bot为独占模式，只有本人可以操作'
        elif await check_super_user_mode():
            has_permission = False
            err_msg = '权限不足，本bot仅允许超级管理员控制'
        elif (await db.get_guild_admin(event.guild_id, event.channel_id, bot.self_id)) or (await (GUILD_ADMIN | SUPERUSER)(bot, event)):
            has_permission = True
    else:
        has_permission = False

    if not has_permission:
        return (False, err_msg)
    
    common_cmd = ['', '查询', 'query', '设定', 'set', '更新', 'update', 'edit', '添加', 'new']
    super_cmd = ['admin', '删除', 'del', 'delete',
                       '锁定', 'lock', '解锁', 'unlock', '拓展', 'ext', '开启', 'on', '关闭', 'off', '重置', 'reset', 'debug', '会话', 'chats',
                       '记忆', 'memory']
    
    is_super_user = await (SUPERUSER)(bot, event)
    is_admin = is_super_user or await (GROUP_ADMIN | GROUP_OWNER)(bot, event)
    
    cmd = args[0]
    if cmd in common_cmd:
        return (is_admin, None if is_admin else '权限不足，只有管理员才允许使用此指令')
    elif cmd in super_cmd:
        return (is_super_user, None if is_super_user else '只有超级管理员才允许使用此指令')
    else:
        return (True, None)
    
    return (True, None)

try:
    import nonebot_plugin_naturel_gpt
    nonebot_plugin_naturel_gpt.set_permission_check_func(permission_check_chatgpt)
except:
    pass