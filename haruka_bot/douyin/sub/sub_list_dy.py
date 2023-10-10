from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent

from ...database import DB as db
from ...utils import get_type_id, on_command, permission_check, to_me
from ... import config

sub_list_dy = on_command("抖音关注列表", aliases={"抖音列表", "抖音订阅列表"}, rule=to_me(), priority=5, block=True)
print(sub_list_dy)
sub_list_dy.__doc__ = """抖音关注列表"""

@sub_list_dy.handle()
async def _(event: GroupMessageEvent, bot: Bot):
    """发送当前位置的订阅列表"""
    message = "抖音关注列表（所有群/好友/bot都是分开的）\n\n"
    subs = await db.get_sub_list_dy(event.group_id, bot.self_id)
    for sub in subs:
        user = await db.get_user_dy(sec_uid=sub.sec_uid)
        if user and user.room_id != 0:
            room_msg = f'({user.room_id})'
        else:
            room_msg = ''
        message += (
            f"{sub.name}{room_msg}\n"
        )
    await sub_list_dy.finish(message.rstrip())
