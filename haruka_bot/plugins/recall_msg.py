from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.plugin import on_keyword
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER

# on_recall = on_keyword({"撤回"}, permission=SUPERUSER)

# @on_recall.handle()
# async def recall_handle(matcher:Matcher, bot: Bot, event: GroupMessageEvent):
#     if event.reply:
#         text = event.get_plaintext().strip()
#         if text != '撤回':
#             return
#         await bot.delete_msg(message_id=event.reply.message_id)
