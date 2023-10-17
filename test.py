import asyncio
import re
from pathlib import Path
from bilireq.live import get_rooms_info_by_uids
from httpx import AsyncClient
# from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.log import logger

#import haruka_bot.config
#from haruka_bot.database import DB as db
#from utils import PROXIES, safe_send, scheduler
    
from dataclasses import dataclass, astuple
import time
from typing import Any, Dict, Mapping, Union

import collections
import time
from playwright.async_api import async_playwright

user_agent = ("Mozilla/5.0 (Linux; Android 11; RMX3161 Build/RKQ1.201217.003; wv) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Version/4.0 Chrome/101.0.4896.59 Mobile Safari/537.36")

async def screenshot(url):
    p = await async_playwright().start()
    browser = await p.chromium.launch(proxy={"server":"per-context"}, headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        proxy={"server": "http://192.168.31.210:10800"},
        device_scale_factor=2,
        user_agent=user_agent,
        viewport={"width": 800, "height": 600},
        )
    page = await context.new_page()

    try:
        await page.goto(
                url,
                wait_until="networkidle",
            )
        await page.add_script_tag(path= str(Path(__file__).parent) + '/haruka_bot/utils/github_page.js')
        await page.evaluate('removeExtraDoms()')

        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(0.1)

        body = await page.query_selector('body')
        body_clip = await body.bounding_box() if body else None
        if body_clip:
            body_clip['x'] = 0.0
            body_clip['y'] = 0.0
        screenshot = await page.screenshot(clip=body_clip, full_page=True)
        Path('./github.png').write_bytes(screenshot)
        print('after screenshot')
        await asyncio.sleep(99999999)

    except Exception as e:
        logger.exception(f"截取github网页时发生错误：{url}")
        return await page.screenshot(full_page=True)
    finally:
        await page.close()
        await context.close()

# asyncio.run(screenshot('https://github.com/linxinrao/Shamrock/blob/master/xposed/src/main/java/moe/fuqiuluo/shamrock/remote/service/WebSocketClientService.kt#L115-L125'))
# asyncio.run(screenshot('https://github.com/linxinrao/Shamrock/issues/104'))
# asyncio.run(screenshot('https://github.com/linxinrao/Shamrock/blob/master/app/build.gradle.kts#L181'))

# assert(re.search('^(/issues/|/pull/|/blob/', 'https://github.com/linxinrao/Shamrock/pull/104'))

text = '撤回'
print(text != '撤回')