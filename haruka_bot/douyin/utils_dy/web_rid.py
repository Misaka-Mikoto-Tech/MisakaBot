# -*- encoding: utf-8 -*-

"""
Author: Hmily
Github:https://github.com/ihmily
Date: 2023-07-17 23:52:05
Update: 2023-09-07 23:35:00
Copyright (c) 2023 by Hmily, All Rights Reserved.
"""
import asyncio
import json
import re
import urllib.parse
import execjs
from httpx import AsyncClient  # pip install PyExecJS
import requests
import urllib.request
from pathlib import Path


no_proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(no_proxy_handler)

headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Cookie': 's_v_web_id=verify_lk07kv74_QZYCUApD_xhiB_405x_Ax51_GYO9bUIyZQVf'
    }


# X-bogus算法
def get_xbogus(url) -> str:
    query = urllib.parse.urlparse(url).query
    xbogus = execjs.compile(open(f"{Path(__file__).parent}/X-Bogus.js").read()).call('sign', query, headers["User-Agent"])
    # print(xbogus)
    return xbogus


# 获取房间ID和用户secID
async def get_sec_user_id_from_live_url(url):
    async with AsyncClient() as client:
        resp = await client.get(
            url, headers=headers,
        )
    redirect_url = resp.headers.get('location')
    sec_user_id=re.search(r'sec_user_id=([\w\d_\-]+)&',redirect_url).group(1)
    room_id=redirect_url.split('?')[0].rsplit('/',maxsplit=1)[1]
    return room_id,sec_user_id


# 获取直播间webID
async def get_live_room_id(room_id,sec_user_id):
    url= f'https://webcast.amemv.com/webcast/room/reflow/info/?verifyFp=verify_lk07kv74_QZYCUApD_xhiB_405x_Ax51_GYO9bUIyZQVf&type_id=0&live_id=1&room_id={room_id}&sec_user_id={sec_user_id}&app_id=1128&msToken=wrqzbEaTlsxt52-vxyZo_mIoL0RjNi1ZdDe7gzEGMUTVh_HvmbLLkQrA_1HKVOa2C6gkxb6IiY6TY2z8enAkPEwGq--gM-me3Yudck2ailla5Q4osnYIHxd9dI4WtQ=='
    xbogus = get_xbogus(url)  # 获取X-Bogus算法
    url = url + "&X-Bogus=" + xbogus
    async with AsyncClient() as client:
        resp = await client.get(
            url, headers=headers,
        )
    resp.encoding = "utf-8"
    json_data = json.loads(resp.text)
    web_rid=json_data['data']['room']['owner']['web_rid']
    return web_rid

async def _test():
    url="https://v.douyin.com/iQLgKSj/"
    # url="https://v.douyin.com/iQFeBnt/"
    # url="https://v.douyin.com/iehvKttp/"
    room_id,sec_user_id = await get_sec_user_id_from_live_url(url)
    web_rid=get_live_room_id(room_id,sec_user_id)
    print(web_rid)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(_test())




