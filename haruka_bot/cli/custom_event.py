from typing import Dict, List, Literal, Optional, Any, Set, Type, TypeVar
from nonebot.log import logger
import nonebot
from nonebot.typing import overrides
from nonebot.utils import escape_tag
from nonebot.adapters.onebot.v11 import Adapter
from nonebot.adapters.onebot.v11.event import Event, MessageEvent, GroupMessageEvent, PrivateMessageEvent
from nonebot.message import event_preprocessor
from nonebot.matcher import Matcher
from nonebot.adapters import Bot
from nonebot.exception import (
    NoLogException,
    StopPropagation,
    IgnoredException,
    SkippedException,
)
from nonebot.adapters import Bot as BaseBot, Event as BaseEvent

Event_T = TypeVar("Event_T", bound=Type[Event])

def register_event(event: Event_T) -> Event_T:
    Adapter.add_custom_model(event)
    logger.opt(colors=True).trace(
        f"Custom event <e>{event.__qualname__!r}</e> registered "
        f"from module <g>{event.__class__.__module__!r}</g>"
    )
    return event


@register_event
class GroupMessageSentEvent(GroupMessageEvent):
    """群消息里自己发送的消息"""

    post_type: Literal['message_sent']
    message_type: Literal["group"]
 
    @overrides(Event)
    def get_type(self) -> str:
        """伪装成message类型。"""
        return "message"
    

msg_sent_set:Set[str] = set() # bot 自己发送的消息

"""消息发送钩子，用于记录自己发送的消息"""
@Bot.on_called_api
async def handle_group_message_sent(bot: Bot, exception: Optional[Exception], api: str, data: Dict[str, Any], result: Any):
    global msg_sent_set
    if result and (api in ['send_msg', 'send_group_msg', 'send_private_msg']):
        msg_id = result.get('message_id', None)
        if msg_id:
            msg_sent_set.add(f"{bot.self_id}_{msg_id}")

@event_preprocessor
async def on_pre_message(event: BaseEvent, bot: BaseBot):
    """拦截消息发送"""
    global msg_sent_set
    need_skip = False
    if isinstance(event, GroupMessageEvent) or isinstance(event, PrivateMessageEvent):
        if event.post_type == 'message_sent': # 通过bot.send发送的消息不处理
            msg_key = f"{bot.self_id}_{event.message_id}"
            if msg_key in msg_sent_set:
                msg_sent_set.remove(msg_key)
                need_skip = True
            
        if len(msg_sent_set) > 10:
            logger.warning(f"累积的待处理的自己发送消息数量为 {len(msg_sent_set)}, 请检查逻辑是否有错误")
            msg_sent_set.clear()

        if need_skip:
            raise IgnoredException("由bot_send发送的消息,取消派发")

__all__ = [
    "GroupMessageSentEvent",
]