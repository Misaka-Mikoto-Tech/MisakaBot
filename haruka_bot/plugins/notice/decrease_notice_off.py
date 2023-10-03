from typing import Union
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot_plugin_guild_patch import GuildMessageEvent

from ...cli.handle_message_sent import GroupMessageSentEvent

from ...database import DB as db
from ...utils import (
    group_only,
    on_command,
    permission_check,
    to_me,
)

decrease_notice_off = on_command("关闭退群通知", rule=to_me(), priority=5, block=True)
decrease_notice_off.__doc__ = """关闭退群通知"""

decrease_notice_off.handle()(permission_check)
decrease_notice_off.handle()(group_only)

@decrease_notice_off.handle()
async def _(event: Union[GroupMessageEvent, GroupMessageSentEvent, GuildMessageEvent], bot:Bot):
    """关闭当前退群通知"""
    if isinstance(event, GuildMessageEvent):
        if await db.set_guild_decrease_notice(event.guild_id, event.channel_id, bot.self_id, False):
            await decrease_notice_off.finish("已关闭退频道通知")
    else:
        if await db.set_group_decrease_notice(event.group_id, bot.self_id, False):
            await decrease_notice_off.finish("已关闭退群通知")
    await decrease_notice_off.finish("退群通知已经关闭了")
