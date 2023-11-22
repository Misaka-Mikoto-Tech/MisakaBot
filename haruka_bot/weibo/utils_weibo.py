
import html
import json
import random
import time
from dateutil import parser
from typing import Any, Tuple
from httpx import AsyncClient
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message

from ..utils.browser import get_weibo_screenshot

headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    }

API_URL = 'https://m.weibo.cn/api/container/getIndex'

class UserInfo:
    uid: int
    user_name: str
    containerid: int
    profile_url: str

async def get_userinfo(uid: int)-> UserInfo:
    """通过uid获取微博用户信息"""
    params = {
        'type': 'uid',
        'value': uid
    }
    async with AsyncClient() as client:
        resp = await client.get(
            API_URL, headers=headers,
            params=params
        )
    resp.encoding = "utf-8"
    resp_json = json.loads(resp.text)
    
    ret = UserInfo()
    ret.uid = uid
    ret.user_name = resp_json['data']['userInfo']['screen_name']
    ret.profile_url = resp_json['data']['userInfo']['profile_url']
    for tab in resp_json['data']['tabsInfo']['tabs']:
        if tab['tab_type'] == 'weibo':
            ret.containerid = tab['containerid']
            break
    
    return ret

async def get_user_dynamics(containerid: int):
    """通过containerid获取动态列表"""
    params = {
        'containerid': containerid,
    }
    async with AsyncClient() as client:
        resp = await client.get(
            API_URL, headers=headers,
            params=params
        )
    resp.encoding = "utf-8"
    resp_json = json.loads(resp.text)
    return resp_json
    # return [dyn for dyn in resp_json['data']['cards'] if dyn['card_type'] == 9] 

async def create_dynamic_msg(dyn: Any) -> Message:
    """生成微博消息"""
    dyn_text = html.unescape(dyn['mblog']['text'])
    dyn_link = html.unescape(dyn['scheme'])
    user_name = html.unescape(dyn['mblog']['user']['screen_name'])
    create_time = parser.parse(dyn['mblog']['created_at']).strftime("%Y-%m-%d %H:%M:%S")

    # 浏览器截图
    shot_image = await get_weibo_screenshot(dyn_link)
    msg: Message = f"{user_name} 刚刚发了一条新微博：\n" + MessageSegment.image(shot_image) + f"\n{dyn_link}"
    return msg
