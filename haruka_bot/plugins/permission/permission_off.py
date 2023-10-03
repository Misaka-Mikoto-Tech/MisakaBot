from typing import Union

from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot_plugin_guild_patch import GuildMessageEvent

from ...cli.handle_message_sent import GroupMessageSentEvent

from ...database import DB as db
from ...utils import GUILD_ADMIN, group_only, on_command, permission_check, to_me
from ...cli.custom_permission import BOT_SELF

permission_off = on_command(
    "关闭权限",
    rule=to_me(),
    #permission=GROUP_OWNER | GROUP_ADMIN | SUPERUSER | GUILD_ADMIN | BOT_SELF,
    priority=5, block=True
)
permission_off.__doc__ = """关闭权限"""

permission_off.handle()(permission_check)
permission_off.handle()(group_only)


@permission_off.handle()
async def _(event: Union[GroupMessageEvent, GroupMessageSentEvent, GuildMessageEvent], bot:Bot):
    """关闭当前群权限"""
    if isinstance(event, GuildMessageEvent):
        if await db.set_guild_permission(event.guild_id, event.channel_id, bot.self_id, False):
            await permission_off.finish("已关闭权限，所有人均可操作")
    else:
        if await db.set_group_permission(event.group_id, bot.self_id, False):
            await permission_off.finish("已关闭权限，所有人均可操作")
    await permission_off.finish("权限已经关闭了，所有人均可操作")
