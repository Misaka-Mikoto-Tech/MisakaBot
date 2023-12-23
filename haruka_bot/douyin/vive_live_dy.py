
# 暂时不实现，因为无法通过抖音用户名获取到直播间号或者直播状态

# from datetime import datetime
# import random
# from typing import List
# from loguru import logger
# from nonebot.matcher import matchers
# from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
# from nonebot.adapters.onebot.v11.event import MessageEvent
# from nonebot.internal.matcher import Matcher, current_event
# from nonebot.params import ArgPlainText, CommandArg
# from bilireq.grpc.dynamic import grpc_get_user_dynamics
# from bilireq.grpc.protos.bilibili.app.dynamic.v2.dynamic_pb2 import DynamicType

# from ..utils import on_command, to_me, text_to_img, PROXIES, safe_send, scheduler, format_time_span, format_time
# from .utils_dy import get_user_dynamics, get_sec_user_id, get_aweme_short_url, create_aweme_msg
# from .. import config
# from .core.dy_api import get_user_info
# from pusher.live_pusher_dy import all_status

# vive_dy = on_command("抖音直播", aliases={"查看抖音直播"}, rule=to_me(), priority=5, block=True) # 数值越小优先级越高
# vive_dy.__doc__ = "抖音直播"

# @vive_dy.handle()
# async def _(
#     matcher: Matcher, event: MessageEvent, bot:Bot, arg_msg: Message = CommandArg()
# ):
#     if arg_msg.extract_plain_text().strip():
#         matcher.set_arg("arg", arg_msg)

# @vive_dy.got("arg", "请发送抖音用户名")
# async def _(
#     matcher: Matcher, event: MessageEvent, bot:Bot, arg: str = ArgPlainText("arg")
# ):
#     vive_text = arg.strip()
#     logger.info(f"接收到抖音直播查询数据:{vive_text}")

#     user_name = vive_text

#     if not (sec_uid := await get_sec_user_id(user_name)):
#         return await vive_dy.send(MessageSegment.at(event.user_id) + " 未找到该 UP，请输入正确的UP 名、UP UID或 UP 首页链接")

#     if isinstance(sec_uid, list):
#         return await vive_dy.send(MessageSegment.at(event.user_id) + f" 未找到 {user_name}, 你是否想要找:\n" + '\n'.join([item['user_info']['nickname'] for item in sec_uid[:10] ]))

    