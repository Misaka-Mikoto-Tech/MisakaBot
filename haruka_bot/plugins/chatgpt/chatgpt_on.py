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

chatgpt_on = on_command("开启ChatGPT",rule=to_me(), priority=5, block=True)
chatgpt_on.__doc__ = """开启ChatGPT"""

chatgpt_on.handle()(permission_check)
chatgpt_on.handle()(group_only)

@chatgpt_on.handle()
async def _(event: Union[GroupMessageEvent, GroupMessageSentEvent, GuildMessageEvent], bot:Bot):
    """开启当前群ChatGPT"""

    # chgpt 设定必须是bot自身或者超级管理员
    if not ((event.sender.user_id == int(bot.self_id)) or (await (SUPERUSER)(bot, event))):
        await chatgpt_on.finish("权限不足，只有bot自身或者超级管理员才允许开启chatgpt")

    if isinstance(event, GuildMessageEvent):
        if await db.set_guild_chatgpt(event.guild_id, event.channel_id, bot.self_id, True):
            await chatgpt_on.finish("已开启当前频道ChatGPT，详细帮助请@bot并发送 rg 查询")
    else:
        if await db.set_group_chatgpt(event.group_id, bot.self_id, True):
            await chatgpt_on.finish("已开启当前群组ChatGPT，详细帮助请@bot并发送 rg 查询")
    await chatgpt_on.finish("ChatGPT已经开启，详细帮助请@bot并发送 rg 查询")
