from typing import Union

from nonebot import on_notice
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11 import GroupDecreaseNoticeEvent
from nonebot_plugin_guild_patch import ChannelDestroyedNoticeEvent
from nonebot.log import logger

from ..database import DB as db

group_decrease_notice = on_notice(priority=5)

@group_decrease_notice.handle()
async def _(event: Union[GroupDecreaseNoticeEvent, ChannelDestroyedNoticeEvent], bot: Bot):
    """有人退群时发通知"""
    if isinstance(event, GroupDecreaseNoticeEvent):
        logger.warning(f"bot:{bot.self_id}: {event.user_id}退出群{event.group_id}")
        if (event.self_id != event.user_id):
            if await db.get_group_decrease_notice(event.group_id, bot.self_id):
                await group_decrease_notice.finish("呜～，有人跑了")
    elif isinstance(event, ChannelDestroyedNoticeEvent):
        logger.warning(f"bot:{bot.self_id}: {event.user_id}退出频道{event.channel_id}")
        if (event.self_id != event.user_id):
            if await db.get_guild_decrease_notice(event.guild_id, event.channel_id, bot.self_id):
                await group_decrease_notice.finish("呜～，有人跑了")
