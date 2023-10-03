import asyncio
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

@Bot.on_called_api
async def handle_group_message_sent(bot: Bot, exception: Optional[Exception], api: str, data: Dict[str, Any], result: Any):
    """消息发送API钩子，用于记录自己发送的消息"""
    global msg_sent_set
    if result and (api in ['send_msg', 'send_group_msg', 'send_private_msg']):
        logger.debug(f"收到发送消息API调用：{api}, result:{result}")
        msg_key = f"{bot.self_id}_{data.get('group_id', 0)}_{data.get('user_id', 0)}_{result.get('seq', 0)}"
        msg_sent_set.add(msg_key)

@event_preprocessor
async def on_pre_message(event: BaseEvent, bot: BaseBot):
    """拦截消息事件派发"""
    global msg_sent_set
    need_skip = False
    if isinstance(event, GroupMessageEvent) or isinstance(event, PrivateMessageEvent):
        # 通过bot.send发送的消息不处理(icqq 只有message, 没有 message_sent)
        if event.post_type in ['message_sent', 'message'] and event.sender.user_id == int(bot.self_id):
            group_id = event.group_id if isinstance(event, GroupMessageEvent) else 0
            msg_key = f"{bot.self_id}_{group_id}_{event.sender.user_id}_{event.__dict__['seq'] or 0}"
            logger.debug(f"预处理发送事件:{msg_key}")

            """
                目前在调用 bot.send 时 go-cqhttp 会立刻返回一个 message_sent 的event，并被派发 `adapter.onebot.v11.adapter.py: _handle_ws`
                此时 Bot.call_api->await self.adapter._call_api() 还没执行完，下面的 self._called_api_hook 尚未执行
                因此出现了 此回调比 Bot.on_called_api 执行还早的现象
                （可能是因为这是在两个线程中执行的，所以handle_ws并不会等待call_api函数执行完毕）
                为了避免这种情况下找不到 message_id, 故等待一下再查找
            """ 
            await asyncio.sleep(0.2)
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