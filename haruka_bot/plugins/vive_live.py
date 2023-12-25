
import json
import asyncio
from pathlib import Path
import time
from typing import List, Tuple
from loguru import logger
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.internal.matcher import Matcher, current_event
from nonebot.params import ArgPlainText, CommandArg
from bilireq.live import get_rooms_info_by_uids

from ..utils import on_command, to_me, text_to_img, PROXIES, safe_send, scheduler, format_time_span, format_time
from ..utils.uid_extract import uid_extract
from ..utils.bilibili_request import get_b23_url
from ..utils import get_dynamic_screenshot, get_user_dynamics
from ..bili_auth import bili_auth
from .. import config
from ..database import DB as db

vive = on_command("查看主播", aliases={"查询主播"}, rule=to_me(), priority=5, block=True) # 数值越小优先级越高
vive.__doc__ = "查看主播 用户名"

@vive.handle()
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg_msg: Message = CommandArg()
):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)

@vive.got("arg", "请发送主播名称")
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg: str = ArgPlainText("arg")
):
    vive_text = arg.strip()
    logger.info(f"接收到查询主播数据:{vive_text}")

    user_name = vive_text

    if not (uid := await uid_extract(user_name)):
        return await vive.send(MessageSegment.at(event.user_id) + " 未找到该 UP，请输入正确的UP 名、UP UID或 UP 首页链接")

    if isinstance(uid, list):
        return await vive.send(MessageSegment.at(event.user_id) + f" 未找到 {user_name}, 你是否想要找:\n" + '\n'.join([item['uname'] for item in uid[:10] ]))
    elif int(uid) == 0:
        return await vive.send(MessageSegment.at(event.user_id) + " UP 主不存在")

    try:
        res = await get_rooms_info_by_uids([uid], reqtype="web", proxies=PROXIES)
        # Path(f"./bili_live_info.json").write_text(json.dumps(res, indent=2,ensure_ascii=False), encoding='utf8')
    except Exception as e:
        logger.error(f"获取开播列表失败: {e}")
        await vive.finish(f'获取 {user_name} 直播状态失败-1')

    if not res:
        await vive.finish(f'获取 {user_name} 直播状态失败-2')
    info = res.get(uid, None)
    if not info:
        await vive.finish(f'获取 {user_name} 直播状态失败-3')
    
    live_status = 0 if info["live_status"] == 2 else info["live_status"]

    name = info["uname"]
    title = ''
    area_name = ''
    cover = ''
    url = ''
    live_on_time: float = 0
    if live_status:  # 正在直播
        room_id = info["short_id"] if info["short_id"] else info["room_id"]
        url = "https://live.bilibili.com/" + str(room_id)
        live_on_time = float(info["live_time"])
        title = info["title"]
        area_name = f"{info['area_v2_parent_name']} - {info['area_v2_name']}"
        cover = (
            info["cover_from_user"] if info["cover_from_user"] else info["keyframe"]
        )

        live_span = format_time_span(time.time() - live_on_time)
        live_msg = (
            f"{name} 正在直播\n已开播 {live_span}\n--------------------\n标题：{title}\n分区：{area_name}\n" + MessageSegment.image(cover) + f"\n{url}"
        )
    else:
        live_msg = f"{name}({uid}) 未开播"
        user = await db.get_user(uid=int(uid)) # 如果是已订阅up，检查上次开播时间
        if user and user.live_on_time > 0:
            live_msg = f"{name}({uid}) 未开播\n上次开播时间 {format_time(user.live_on_time)}\上次直播时长 {format_time_span(user.live_off_time - user.live_on_time)}"

    await vive.finish(live_msg)