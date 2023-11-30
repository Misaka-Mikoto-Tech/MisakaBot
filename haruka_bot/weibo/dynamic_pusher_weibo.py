import asyncio
import random
import pathlib
import time
import json
import html
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
from ..utils import scheduler, safe_send
from ..database import DB as db
from ..database import dynamic_offset_weibo as offset_weibo
from .utils_weibo import get_userinfo, get_user_dynamics, create_dynamic_msg

async def weibo_sched():
    """微博动态推送"""

    global offset_weibo

    uid = await db.next_uid_weibo("dynamic")
    if not uid:
        # 没有订阅先暂停一秒再跳过，不然会导致 CPU 占用过高
        await asyncio.sleep(1)
        return
    await asyncio.sleep(random.uniform(9, 25)) # 随机等待几秒钟，防止被风控

    user_info = await db.get_user_weibo(uid=uid)
    if not user_info:
        return

    logger.debug(f"爬取微博动态 {user_info.name}（{uid}）")

    try:
        dynamics = await get_user_dynamics(user_info.containerid)
        if dynamics is None:
            return
    except Exception as e:
        logger.error(f"获取微博用户动态失败, {e.args}")
        return
    
    dynamic_list = dynamics['data']['cards'] if "cards" in dynamics['data'] else None
    if not dynamic_list:
        logger.debug(f'用户 {user_info.name} 未发布任何微博')
        return
    
    dynamic_list = [dyn for dyn in dynamic_list if dyn['card_type'] == 9] # 暂时不知道其它类型是什么意思
    dynamic_list = sorted(dynamic_list, key=lambda x: int(x["mblog"]["id"]), reverse=True)

    # 此处假设单个用户不会在一轮循环中发布多条微博，因此只取第一条
    latest_dyn = dynamic_list[0]
    latest_dyn_id = int(latest_dyn["mblog"]["id"])

    last_dyn_id = offset_weibo[uid]
    if last_dyn_id == -1: # 首次爬取当前用户，跳过
        offset_weibo[uid] = latest_dyn_id
        return
    
    if latest_dyn_id > last_dyn_id:
        offset_weibo[uid] = latest_dyn_id
    else:
        return
    
    # dyn_text = latest_dyn['mblog']['text']
    dyn_link = latest_dyn['scheme']
    logger.info(f"{user_info.name} 发布了新微博 {dyn_link}")

    msg: Message = await create_dynamic_msg(latest_dyn)
    push_list = await db.get_push_list_weibo(uid)
    for sets in push_list:
        await safe_send(
            bot_id=sets.bot_id,
            send_type='group',
            type_id=sets.group_id,
            message=msg,
            at=False,
            prefix=None,
        )


def weibo_dynamic_lisener(event):
    if hasattr(event, "job_id") and event.job_id != "weibo_dynamic_sched":
        return
    job = scheduler.get_job("weibo_dynamic_sched")
    if not job:
        scheduler.add_job(
            weibo_sched, id="weibo_dynamic_sched", next_run_time=datetime.now(scheduler.timezone)
        )

scheduler.add_listener(
    weibo_dynamic_lisener,
    EVENT_JOB_EXECUTED
    | EVENT_JOB_ERROR
    | EVENT_JOB_MISSED
    | EVENT_SCHEDULER_STARTED,
)

