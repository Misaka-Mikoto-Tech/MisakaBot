from typing import Union

# from nonebot import on_notice
# from nonebot.adapters.onebot.v11 import Bot
# from nonebot.adapters.onebot.v11 import GroupDecreaseNoticeEvent
# from nonebot_plugin_guild_patch import ChannelDestroyedNoticeEvent

# from ..database import DB as db
# from ..utils import get_type_id

# group_decrease = on_notice(priority=5)


# @group_decrease.handle()
# async def _(event: Union[GroupDecreaseNoticeEvent, ChannelDestroyedNoticeEvent], bot: Bot):
#     """退群时，自动删除该群订阅列表"""
#     if isinstance(event, GroupDecreaseNoticeEvent):
#         if event.self_id == event.user_id:
#             await db.delete_sub_list(type="group", type_id=event.group_id, bot_id=bot.self_id)
#             await db.delete_group(group_id=event.group_id)
#     elif isinstance(event, ChannelDestroyedNoticeEvent):
#         await db.delete_sub_list(type="guild", type_id=await get_type_id(event), bot_id=bot.self_id)
#         await db.delete_guild(guild_id=await get_type_id(event))
