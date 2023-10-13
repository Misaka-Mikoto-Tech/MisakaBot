
from datetime import datetime
import random
from typing import List
from loguru import logger
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.internal.matcher import Matcher, current_event
from nonebot.params import ArgPlainText, CommandArg
from bilireq.grpc.dynamic import grpc_get_user_dynamics
from bilireq.grpc.protos.bilibili.app.dynamic.v2.dynamic_pb2 import DynamicType

from ..utils import on_command, to_me, text_to_img
from .utils_dy import get_user_dynamics, get_sec_user_id, get_aweme_short_url, create_aweme_msg
from .. import config
from .core.dy_api import get_user_info

vive_dy = on_command("查看抖音", aliases={"查询抖音", "抖音动态"}, rule=to_me(), priority=5, block=True) # 数值越小优先级越高
vive_dy.__doc__ = "查看抖音"

@vive_dy.handle()
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg_msg: Message = CommandArg()
):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)

@vive_dy.got("arg", "请发送抖音用户名")
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg: str = ArgPlainText("arg")
):
    vive_texts = arg.strip().split(' ')
    logger.info(f"接收到抖音查询数据:{vive_texts}")

    user_name = vive_texts[0]
    if not (sec_uid := await get_sec_user_id(user_name)):
        return await vive_dy.send(MessageSegment.at(event.user_id) + " 未找到该 UP，请输入正确的UP 名、UP UID或 UP 首页链接")

    if isinstance(sec_uid, list):
        return await vive_dy.send(MessageSegment.at(event.user_id) + f" 未找到{user_name}, 你是否想要找:\n" + '\n'.join([item['user_info']['nickname'] for item in sec_uid[:10] ]))

    # await get_user_info(sec_uid)
    dynamics = await get_user_dynamics(sec_uid, user_name)
    if not dynamics:
        return await vive_dy.send(MessageSegment.at(event.user_id) + f" 查看抖音用户 {user_name} 失败")

    aweme_list = dynamics["aweme_list"] if "aweme_list" in dynamics else None
    if not aweme_list:
        return await vive_dy.send("该 UP 未发布任何作品")
    
    aweme_list = sorted(aweme_list, key=lambda x: int(x["aweme_id"]), reverse=True)
    offset_num = int(vive_texts[1]) if len(vive_texts) > 1 else 0

    try:
        dyn = aweme_list[offset_num]
    except IndexError:
        return await vive_dy.send(MessageSegment.at(event.user_id) + " 你输入的数字过大，该 UP 的最后一页动态没有这么多条")
    
    # ios 要求第一个字符必须是数字才允许app读取剪贴板
    return await vive_dy.send(f'{random.randint(1, 9)} ' + MessageSegment.at(event.user_id) + await create_aweme_msg(dyn))
