from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.plugin import on_command
from ..utils import permission_check

on_recall = on_command("撤回", aliases={"recall", "delete"}, priority=5, block=True)
on_recall.__doc__ = "撤回消息"

on_recall.handle()(permission_check)

@on_recall.handle()
async def recall_handle(bot: Bot, event: GroupMessageEvent):
    if event.reply:
        await bot.delete_msg(message_id=event.reply.message_id)
