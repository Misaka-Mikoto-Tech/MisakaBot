import asyncio
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

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
url = "https://www.douyin.com/aweme/v1/web/web_shorten/?target=https://www.iesdouyin.com/share/video/7258254932447366440/?region=CN&mid=7258254958867532599&u_code=e9b6543hh1k4jg&did=MS4wLjABAAAAXgYwX7crTH3d-Vw9brUbRagOb1yVOium7_TUF6EXFsrJKWvBO19BN2W30JkyIh6y&iid=MS4wLjABAAAANwkJuWIRFOzg5uCpDRpMj4OX-QryoDgn-yYlXQnRwQQ&with_sec_did=1&titleType=title&share_sign=dDXiwWmXzooRo_4DD2KybN2bKiKjFhO_tmXEFJ94jKE-&share_version=190500&ts=1691457945&from_ssr=1&from=web_code_link&belong=aweme&persist=1&device_platform=webapp&aid=6383&channel=channel_pc_web&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=2560&screen_height=1440&browser_language=en-US&browser_platform=Win32&browser_name=Chrome&browser_version=102.0.0.0&browser_online=true&engine_name=Blink&engine_version=102.0.0.0&os_name=Windows&os_version=10&cpu_core_num=16&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=0&webid=7264479485251339816&msToken=OQXJaryNzwCkJ-vPNLlQe5OZ15DOlDc1Nlth5I5y44ZKeHcaFJ-sITEfVkb-c6I5KuL5cYXfj2IbaJ2RWKux2_AQuEegIG7AL2VXM7tMB1QnU-7RsrGb-CUPGuHq"
# &X-Bogus=DFSzswVuyqtANHrFt9XUJYXAIQR2"

async def gen_x_bogus():
    gen_url = "http://127.0.0.1:8787/X-Bogus"
    # data = {"url": url, "user_agent": user_agent}
    data = {
    "url":"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7190049956269444386&aid=1128&version_name=23.5.0&device_platform=android&os_version=2333",
    "user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
    }
    async with AsyncClient() as client:
        resp = await client.request(
            "post", gen_url, json=data
        )
    resp.encoding = "utf-8"
    print(resp.text)

# asyncio.run(gen_x_bogus())

lst = None
print(not lst)