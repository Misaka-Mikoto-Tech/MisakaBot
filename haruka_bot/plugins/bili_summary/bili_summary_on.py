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

bili_summary_on = on_command("开启视频解析",rule=to_me(), priority=5, block=True)
bili_summary_on.__doc__ = """开启视频解析"""

bili_summary_on.handle()(permission_check)
bili_summary_on.handle()(group_only)

@bili_summary_on.handle()
async def _(event: Union[GroupMessageEvent, GroupMessageSentEvent, GuildMessageEvent], bot:Bot):
    """开启当前群B站视频解析"""

    if not ((event.sender.user_id == int(bot.self_id))
            or (await (GROUP_ADMIN)(bot, event)) or (await (GUILD_ADMIN)(bot, event))
            or (await (SUPERUSER)(bot, event))):
        await bili_summary_on.finish("权限不足，只有bot自身或者管理员才允许开启B站视频解析")

    if isinstance(event, GuildMessageEvent):
        if await db.set_guild_bili_summary(event.guild_id, event.channel_id, bot.self_id, True):
            await bili_summary_on.finish("已开启当前频道B站视频解析")
    else:
        if await db.set_group_bili_summary(event.group_id, bot.self_id, True):
            await bili_summary_on.finish("已开启当前群组B站视频解析")
    await bili_summary_on.finish("B站视频解析已经开启")
