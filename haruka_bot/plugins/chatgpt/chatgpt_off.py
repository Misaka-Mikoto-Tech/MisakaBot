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

chatgpt_off = on_command("关闭ChatGPT",rule=to_me(), priority=5, block=True)
chatgpt_off.__doc__ = """关闭ChatGPT"""

chatgpt_off.handle()(permission_check)
chatgpt_off.handle()(group_only)

@chatgpt_off.handle()
async def _(event: Union[GroupMessageEvent, GroupMessageSentEvent, GuildMessageEvent], bot:Bot):
    """关闭当前群ChatGPT"""
    if isinstance(event, GuildMessageEvent):
        if await db.set_guild_chatgpt(event.guild_id, event.channel_id, bot.self_id, False):
            await chatgpt_off.finish("已关闭当前频道ChatGPT")
    else:
        if await db.set_group_chatgpt(event.group_id, bot.self_id, False):
            await chatgpt_off.finish("已关闭当前群组ChatGPT")
    await chatgpt_off.finish("ChatGPT已经关闭了")
