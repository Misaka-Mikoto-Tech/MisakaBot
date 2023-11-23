
import html
import json
import random
import time
from dateutil import parser
from urllib import parse
from typing import Any, List, Tuple, Union
from httpx import AsyncClient
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.internal.matcher import Matcher
from nonebot.log import logger

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

async def search_weibo_user(q: str) -> Union[UserInfo, List[str], None]:
    """搜索微博用户名, 找不到时返回可能的用户列表"""
    """
    '3','用户'
    '1','综合'
    '62','关注'
    '61','实时'
    '64','视频'
    '58','问答'
    '21','文章'
    '63','图片'
    '97','同城'
    '60','热门'
    '38','话题'
    '98','超话'
    '32','主页'
    """
    firstParam = f'100103type=3&q={q}&t=0'
    firstParam = parse.quote(firstParam)
    params = {
        'containerid':firstParam,
        'page_type':'searchall',
        'page':0
    }

    try:
        async with AsyncClient() as client:
            resp = await client.get(
                API_URL, headers=headers,
                params=params
            )
        resp.encoding = "utf-8"
        resp_json = json.loads(resp.text)
        cards = resp_json['data']['cards']
    except Exception as e:
        logger.error(f'搜索微博用户失败: {e.args}')
        return None
    
    users: List[str] = list()
    for card in cards:
        if card['card_type'] != 11:
            continue
        card_group = card['card_group']
        for card2 in card_group:
            if card2['card_type'] != 10:
                continue
            user = card2['user']
            if user['screen_name'] == q:
                user_info = UserInfo()
                user_info.uid = user['id']
                user_info.user_name = q
                user_info.profile_url = str(user['profile_url']).split('?')[0]
                return user_info
            users.append(user['screen_name'])
        return users

    return None

async def set_uid_arg_by_q(matcher: Matcher, q: str):
    """通过查询字符串给 Matcher 设置 uid 参数，出现异常会直接终止 matcher"""
    if q.isdigit():
        matcher.set_arg("uid", Message(MessageSegment.text(q)))
    else: # 用户输入了用户名，去搜索uid
        search_resp = await search_weibo_user(q)
        if not search_resp:
            await matcher.finish(f'未找到用户 {q}')
        else:
            if isinstance(search_resp, list):
                await matcher.finish(f"未找到用户 {q}, 你是否想要找:\n" + '\n'.join(search_resp))
            else:
                matcher.set_arg("uid", Message(MessageSegment.text(str(search_resp.uid))))

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
    # dyn_text = dyn['mblog']['text']
    # create_time = parser.parse(dyn['mblog']['created_at']).strftime("%Y-%m-%d %H:%M:%S")
    dyn_link = dyn['scheme']
    dyn_link = str(dyn_link).split('?')[0]
    user_name = dyn['mblog']['user']['screen_name']

    # 浏览器截图
    shot_image = await get_weibo_screenshot(dyn_link)
    msg: Message = f"{user_name} 发了一条新微博：\n" + MessageSegment.image(shot_image) + f"\n{dyn_link}"
    return msg
