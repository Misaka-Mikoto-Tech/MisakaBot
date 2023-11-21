from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent

from ...database import DB as db
from ...utils import get_type_id, on_command, permission_check, to_me
from ... import config

sub_list_weibo = on_command("微博关注列表", aliases={"微博列表", "微博订阅列表"}, rule=to_me(), priority=5, block=True)
sub_list_weibo.__doc__ = """微博关注列表"""

@sub_list_weibo.handle()
async def _(event: GroupMessageEvent, bot: Bot):
    """发送当前位置的订阅列表"""
    message = "微博关注列表（所有群/好友/bot都是分开的）\n\n"
    subs = await db.get_sub_list_weibo(event.group_id, bot.self_id)
    for sub in subs:
        message += f"{sub.name}({sub.uid})\n"
    await sub_list_weibo.finish(message.rstrip())
