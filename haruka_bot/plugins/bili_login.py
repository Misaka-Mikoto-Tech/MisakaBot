import asyncio
import json
import io
import random
from typing import List, Optional
from pathlib import Path
from nonebot import logger
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import MessageEvent
from apscheduler.job import Job

from ..utils import on_command, to_me, text_to_img
from ..version import __version__
from .. import config
from ..utils import (
    PROXIES,
    get_type_id,
    handle_uid,
    on_command,
    permission_check,
    to_me,
    uid_check,
)

from ..bili_auth import bili_auth
from ..utils import get_dynamic_screenshot, safe_send, scheduler
from bilireq.login import Login
from bilireq.exceptions import ResponseCodeError
from bilireq.auth import Auth

bili_login = on_command("bili_login", aliases={"登录B站"}, rule=to_me(), priority=5, block=True) # 数值越小优先级越高
bili_login.handle()(permission_check)

@bili_login.handle()
async def _(event: MessageEvent, bot:Bot):
    logger.info("收到登录B站指令")

    bilibili_login = Login()
    try:
        qr_url = await bilibili_login.get_qrcode_url()
        logger.info(f"登录B站Url:{qr_url}")
        data = await bilibili_login.get_qrcode(qr_url)
        if isinstance(data, bytes):
            await bili_login.send(MessageSegment.image(data))
        else:
            buf = io.BytesIO()
            data.save(buf, format="PNG") # PilImage
            await bili_login.send(MessageSegment.image(buf))
            
        auth_data = await bilibili_login.qrcode_login(interval=5)
        if auth_data:
            bili_auth.set_auth(auth_data)
        logger.success("[BiliBili推送] 二维码登录完成")
        await bili_login.send("[BiliBili推送] 二维码登录完成")
    except ResponseCodeError as e:
        bili_auth.is_logined = False
        err_msg = f"[BiliBili推送] 二维码登录失败：{e.code}，{e.msg}"
        logger.error(err_msg)
        await bili_login.finish(err_msg)

    if bili_auth.auth:
        logger.debug(await bili_auth.auth.get_info())

        login_cache_file = Path(config.haruka_login_cache_file)
        login_cache_file.write_text(
            json.dumps(dict(bili_auth.auth), indent=2, ensure_ascii=False)
        )
        logger.info("[Bilibili推送] 登录完成")
    else:
        logger.error("[Bilibili推送] 登录失败")


_on_start_job: Optional[Job] = None

async def _load_login_cache():
    """尝试从配置文件中加载并自动登录"""
    global _on_start_job

    if _on_start_job:
        _on_start_job.remove()
        _on_start_job = None
    else:
        await asyncio.sleep(random.uniform(1000, 3000)) # 非第一次调用随机延迟一段时间
    
    logger.info("尝试自动登录B站")
    login_cache_file = Path(config.haruka_login_cache_file)
    if login_cache_file.exists():
        auth_data = Auth()
        auth_data.update(json.loads(login_cache_file.read_text()))
        try:
            auth_data = await auth_data.refresh()
            if auth_data:
                bili_auth.set_auth(auth_data)
                login_cache_file.write_text(
                    json.dumps(dict(auth_data), indent=2, ensure_ascii=False)
                )
            
            logger.debug(bili_auth.auth)
            logger.success("[Bilibili推送] 缓存登录完成")
        except ResponseCodeError as e:
            logger.error(f"[Bilibili推送] 缓存登录失败, 请尝试手动登录")
    else:
        logger.error(f"[Bilibili推送] 不存在登录缓存文件, 请尝试手动登录")

_on_start_job = scheduler.add_job(
        _load_login_cache, "interval", seconds=1, id="bili_login_sched_on_start"
    )

scheduler.add_job(
        _load_login_cache, "interval", seconds=12 * 3600 + 500, id="bili_login_sched"
    )

