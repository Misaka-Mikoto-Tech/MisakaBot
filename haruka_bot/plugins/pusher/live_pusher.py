import asyncio
from bilireq.live import get_rooms_info_by_uids
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.log import logger

from ... import config
from ...database import DB as db
from ...database.models import User
from ...utils import PROXIES, safe_send, scheduler, format_time_span

from dataclasses import dataclass, astuple
import time
from typing import Dict
from ...bili_auth import bili_auth

@scheduler.scheduled_job("interval", seconds=config.haruka_live_interval, id="live_sched")
async def live_sched():
    """直播推送"""
    await _check_inited()

    uids = await db.get_uid_list("live")
    if not uids:  # 订阅为空
        return
    try:
        res = await get_rooms_info_by_uids(uids, reqtype="web", proxies=PROXIES)
    except Exception as e:
        logger.error(f"获取开播列表失败: {e}")
        return

    if not res:
        return
    for uid, info in res.items():
        user = await db.get_user(uid=uid)
        assert(user)
        new_status = 0 if info["live_status"] == 2 else info["live_status"]
        # bot启动后第一次轮询到
        if user.live_status == -1:
            live_on_time = float(info['live_time']) if new_status else 0 # 只有开播时获取的时间才有意义, 非直播时B站会乱填这个值
            if live_on_time > 0: # 更新数据库
                await db.update_user(uid=int(uid), live_on_time = live_on_time, live_status=new_status)
            else:
                await db.update_user(uid=int(uid), live_status=new_status)
            continue
        if new_status == user.live_status:  # 直播间状态无变化
            continue

        name = info["uname"]
        title = ''
        area_name = ''
        cover = ''
        url = ''
        if new_status:  # 开播
            room_id = info["short_id"] if info["short_id"] else info["room_id"]
            url = "https://live.bilibili.com/" + str(room_id)
            title = info["title"]
            area_name = f"{info['area_v2_parent_name']} - {info['area_v2_name']}"
            cover = (
                info["cover_from_user"] if info["cover_from_user"] else info["keyframe"]
            )
            logger.info(f"检测到开播：{name}（{uid}）")

            live_msg = (
                f"{name} 正在直播\n--------------------\n标题：{title}\n分区：{area_name}\n" + MessageSegment.image(cover) + f"\n{url}"
            )
        else:  # 下播
            logger.info(f"检测到下播：{name}（{uid}）")
            if not config.haruka_live_off_notify:  # 没开下播推送
                continue
            if user.live_on_time > 0:
                live_msg = f"{name} 下播了\n本次直播时长 {format_time_span(time.time() - user.live_on_time)}"
            else:
                live_msg = f"{name} 下播了"

        # 更新数据库用户信息
        if new_status:
            await db.update_user(int(uid), name=name, live_on_time=float(info['live_time']), live_status=new_status)
        else:
            await db.update_user(int(uid), name=name, live_off_time=time.time(), live_status=new_status)

        # 推送
        push_list = await db.get_push_list(uid, "live")
        for sets in push_list:
            real_live_msg = live_msg
            if new_status and sets.live_tips:
                # 自定义开播提示词
                real_live_msg = f"{sets.live_tips}\n--------------------\n标题：{title}\n分区：{area_name}\n" + MessageSegment.image(cover) + f"\n{url}"
            await safe_send(
                bot_id=sets.bot_id,
                send_type=sets.type,
                type_id=sets.type_id,
                message=real_live_msg,
                at=bool(sets.at) if new_status else False,  # 下播不@全体
            )
            await asyncio.sleep(0.7)
        
inited: bool = False
async def _check_inited():
    global inited
    if not inited:
        await User.update_all(live_status = -1) # bot 启动时状态统一设置为 -1
        inited = True