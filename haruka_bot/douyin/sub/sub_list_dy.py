from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent
from nonebot.params import ArgPlainText, CommandArg

from ...database import DB as db
from ...utils import get_type_id, on_command, permission_check, to_me
from ... import config

sub_list_dy = on_command("抖音关注列表", aliases={"抖音列表", "抖音订阅列表"}, rule=to_me(), priority=5, block=True)
print(sub_list_dy)
sub_list_dy.__doc__ = """抖音关注列表"""

@sub_list_dy.handle()
async def _(event: GroupMessageEvent, bot: Bot, arg: Message = CommandArg()):
    """发送当前位置的订阅列表"""
    arg_text = arg.extract_plain_text().strip()
    debug_mode = arg_text == "debug"

    message = "抖音关注列表（所有群/好友/bot都是分开的）\n\n"
    subs = await db.get_sub_list_dy(event.group_id, bot.self_id)
    for sub in subs:
        user = await db.get_user_dy(sec_uid=sub.sec_uid)
        if user and user.room_id != 0:
            room_msg = f'({user.room_id})'
        else:
            room_msg = ''
        message += (
                f"{sub.name}{room_msg} at:{'开' if sub.at else '关'}"
            )
        if debug_mode:
            message += f", sec_uid:{sub.sec_uid}, live_url:{user.live_url if user else '[no user]'} \n"
        else:
            message += "\n"
    await sub_list_dy.finish(message.rstrip())
