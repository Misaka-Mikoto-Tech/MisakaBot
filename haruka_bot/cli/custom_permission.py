"""只允许Bot自身等权限定义。
"""

from typing import Union
from nonebot.permission import Permission
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import Event, MessageEvent, GroupMessageEvent, Anonymous
from nonebot_plugin_guild_patch import GuildMessageEvent
from .handle_message_sent import GroupMessageSentEvent


async def _group_bot_self(event: Union[GroupMessageEvent, GroupMessageSentEvent, GuildMessageEvent], bot:Bot) -> bool:
    return event.sender.user_id == int(bot.self_id)

BOT_SELF: Permission = Permission(_group_bot_self)
"""匹配机器人自己发送的群聊消息类型事件"""

__all__ = [
    "BOT_SELF",
]
