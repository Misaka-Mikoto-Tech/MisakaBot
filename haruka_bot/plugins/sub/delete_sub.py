from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.params import ArgPlainText, CommandArg
from nonebot.internal.matcher import Matcher, current_event
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message

from ...database import DB as db
from ...utils import (
    get_type_id,
    handle_uid,
    on_command,
    permission_check,
    to_me,
    uid_check,
)

delete_sub = on_command("取关", aliases={"删除主播"}, rule=to_me(), priority=5, block=True)
delete_sub.__doc__ = """取关 用户名"""

delete_sub.handle()(permission_check)

@delete_sub.handle()
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg_msg: Message = CommandArg()
):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("user_name", arg_msg)

@delete_sub.got("user_name", "请发送UP名称")
async def _(event: MessageEvent, bot: Bot, user_name: str = ArgPlainText("user_name")):
    """根据 用户名 删除 UP 主订阅"""
    user_name = user_name.strip()
    uid = getattr(await db.get_user(name=user_name), "uid", None)
    if uid:
        result = await db.delete_sub(
            uid=uid, type=event.message_type, type_id=await get_type_id(event), bot_id=bot.self_id
        )
    else:
        result = False

    if result:
        await delete_sub.finish(f"已取关 {user_name}（{uid}）")
    await delete_sub.finish(f"UID（{uid}）未关注")
