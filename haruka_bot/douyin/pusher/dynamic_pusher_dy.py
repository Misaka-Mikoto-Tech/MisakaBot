import asyncio
import random
import pathlib
import time
import json
from pathlib import Path
from datetime import datetime
from httpx import AsyncClient
from typing import Dict, Union, Optional
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message

from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    EVENT_SCHEDULER_STARTED,
)

from nonebot.log import logger
from ...utils import scheduler, safe_send
from ...database import DB as db
from ...database import dynamic_offset_dy as offset_dy
from ..utils_dy import get_dict_cookies_from_file, get_aweme_short_url, get_user_dynamics, create_aweme_msg, get_sec_user_id

# users = [{"name":"一千夏🥥", "sec_uid":"MS4wLjABAAAALUW2eoJvmC2Q29Qhv82Db8S8V6dWMczwQfqEc1-XFaS2yxMn7oGFcJHnTkOUZAzC"}]

async def dy_sched():
    """抖音动态推送"""

    global offset_dy

    sec_uid: str = str(await db.next_uid_dy("dynamic"))
    if not sec_uid or (sec_uid not in offset_dy): # 未找到或已删除
        # 没有订阅先暂停一秒再跳过，不然会导致 CPU 占用过高
        await asyncio.sleep(1)
        return
    await asyncio.sleep(random.uniform(10, 30)) # 随机等待几秒钟，防止被风控

    user_name = await db.get_user_dy(sec_uid=sec_uid)
    user_name = user_name.name if user_name else ''

    logger.debug(f"爬取抖音动态 {user_name}（{sec_uid}）")

    dynamics = await get_user_dynamics(sec_uid, user_name)
    if dynamics is None:
        return
    
    aweme_list = dynamics["aweme_list"] if "aweme_list" in dynamics else None
    if not aweme_list:
        logger.debug(f'用户 {user_name} 未发布任何动态')
        return
    
    aweme_list = sorted(aweme_list, key=lambda x: int(x["aweme_id"]), reverse=True)

    # 此处假设单个用户不会在一轮循环中发布多条动态，因此只取第一条
    latest_aweme = aweme_list[0]
    latest_aweme_id = int(latest_aweme['aweme_id']) # 貌似 aweme_id 和 create_time 都可以用来判断先后顺序？

    last_aweme_id = offset_dy[sec_uid]
    if last_aweme_id == -1: # 首次爬取当前用户，跳过
        offset_dy[sec_uid] = latest_aweme_id
        return
    
    if latest_aweme_id > last_aweme_id:
        desc = str(latest_aweme['desc']).split('\n') # desc 有两行，第二行为 tag 列表
        offset_dy[sec_uid] = latest_aweme_id
        await db.update_user_dy(sec_uid, latest_aweme['author']['nickname'])
    else:
        return
    
    logger.info(f"{user_name} 发布了新动态 {desc}")

    msg: Message = await create_aweme_msg(latest_aweme)
    push_list = await db.get_push_list_dy(sec_uid)
    for sets in push_list:
        await safe_send(
            bot_id=sets.bot_id,
            send_type='group',
            type_id=sets.group_id,
            message=msg,
            at=False,
        )


def dy_dynamic_lisener(event):
    if hasattr(event, "job_id") and event.job_id != "dy_dynamic_sched":
        return
    job = scheduler.get_job("dy_dynamic_sched")
    if not job:
        scheduler.add_job(
            dy_sched, id="dy_dynamic_sched", next_run_time=datetime.now(scheduler.timezone)
        )

scheduler.add_listener(
    dy_dynamic_lisener,
    EVENT_JOB_EXECUTED
    | EVENT_JOB_ERROR
    | EVENT_JOB_MISSED
    | EVENT_SCHEDULER_STARTED,
)

