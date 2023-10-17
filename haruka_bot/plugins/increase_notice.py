from nonebot import on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent
from nonebot.adapters.onebot.v11.message import Message, MessageSegment

# group_increase_notice = on_notice(priority=5)

# @group_increase_notice.handle()
# async def _(bot: Bot, event: GroupIncreaseNoticeEvent):
#     """有人加群时发欢迎词"""
    
#     group_name = (await bot.get_group_info(group_id=event.group_id))['group_name']
#     # nickname = (await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id))['nickname']

#     message: Message = '欢迎 ' + MessageSegment.at(event.user_id) + f' 加入 {group_name}' # 欢迎词自由发挥
#     await group_increase_notice.finish(message)
