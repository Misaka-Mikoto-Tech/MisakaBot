import asyncio
import os
import re
import sys
import json
import time
import random
import urllib.parse
import execjs
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Union, Optional
from httpx import AsyncClient
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message

from ...database.models import User_dy
from .cookie_utils import auto_get_cookie
from ..core.dy_api import get_random_ua, get_request_headers
from ..core.room_info import RoomInfo
from ..utils_dy.web_rid import get_sec_user_id_from_live_url, get_live_room_id

REQ_SUFFIX = "&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=Win32&browser_name=Chrome&browser_version=102.0.0.0&browser_online=true&engine_name=Blink&engine_version=102.0.0.0&os_name=Windows&os_version=10&cpu_core_num=12&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'

_sec_user_id_cache:Dict[str, str] = {}
async def get_sec_user_id(user_name:str)-> Union[Optional[str], List[Any]]:
    """获取抖音用户的 sec_user_id"""
    #  另外一个搜索接口，只返回一个结果和最新的动态信息'http://api.xn--7gqa009h.top/api/dyss?msg=' + encodeURI(msg), type: 'json' 
    if user_name in _sec_user_id_cache:
        return _sec_user_id_cache[user_name]

    user_name_encoded = urllib.parse.quote(user_name)
    url = ('https://www.douyin.com/aweme/v1/web/discover/search/?device_platform=webapp&aid=6383&channel=channel_pc_web&search_channel=aweme_user_web&keyword='
           + user_name_encoded
           + '&search_source=normal_search&query_correct_type=1&is_filter_search=0&from_group_id=&offset=0&count=12'
           + REQ_SUFFIX)
    url = add_xbogus(url)

    headers = {
        'referer': f'https://www.douyin.com/search/{user_name_encoded}?type=user',
        'User-Agent': USER_AGENT
    }

    try:
        async with AsyncClient() as client:
            resp = await client.get(
                url, headers=headers, cookies=get_dict_cookies_from_file(),
            )
        resp.encoding = "utf-8"
        resp = json.loads(resp.text)
        # Path(f"./douyin_user_search.json").write_text(json.dumps(resp, indent=2,ensure_ascii=False), encoding='utf8')
        if 'user_list' in resp:
            user_list:List[Any] = resp['user_list']
            for user in user_list:
                if user['user_info']['nickname'] == user_name:
                    sec_uid = user['user_info']['sec_uid']
                    _sec_user_id_cache[user_name] = sec_uid # 匹配成功，缓存并返回
                    return sec_uid
            # 没有完全匹配的，直接把列表返回
            return user_list
        return None
    except Exception as e:
        logger.error(f'获取抖音sec_user_id失败，可能是cookie 或 X-Bogus失效: {e}')
        return None


def get_list_cookies_from_file() -> List[Any]:
    """从文件读取list格式的cookie"""
    cookies = list()
    try:
        cookies_raw = json.loads(Path('./dy_cookie.json').read_text("utf-8"))  # type: ignore
        cookies = [{ "name":ck["name"], "value":ck["value"], "path":ck["path"], "domain": ck["domain"] }
                    for ck in cookies_raw]
    except Exception as e:
        logger.error(f"读取cookie文件失败:{e}")

    return cookies

def get_dict_cookies_from_file() -> Dict[str, Any]:
    """从文件读取dict格式的cookie"""
    cookies_list = get_list_cookies_from_file()
    cookies_dict = {ck['name']:ck['value'] for ck in cookies_list}
    return cookies_dict

async def get_user_dynamics(sec_user_id: str, name: str):
    """获取指定用户的json类型动态数据"""

    # 尝试查询动态前先访问下主页以避免风控
    url = 'https://www.douyin.com/user/' + sec_user_id

    headers = {
        'referer': 'https://www.douyin.com/user/' + sec_user_id,
        'User-Agent': USER_AGENT
    }

    resp = None
    try:
        async with AsyncClient() as client:
            resp = await client.get(
                url, headers=headers, cookies=get_dict_cookies_from_file(),
            )
        resp.encoding = "utf-8"
        if len(resp.text.strip()) == 0:
            raise Exception('respone content is empty')
    except Exception as e:
        logger.error(f'访问抖音用户主页失败，可能被风控: {e} id:{name}')
        return None


    url = ('https://www.douyin.com/aweme/v1/web/aweme/post/?device_platform=webapp&aid=6383&channel=channel_pc_web&sec_user_id=' + sec_user_id
           +'&max_cursor='
           + str(int(round(time.time() * 1000)))
           + '&locate_query=false&show_live_replay_strategy=1&count=18&cut_version=1&publish_video_strategy_type=2'
        + REQ_SUFFIX)
    url = add_xbogus(url)

    resp_is_empty = False
    try:
        async with AsyncClient() as client:
            resp = await client.get(
                url, headers=headers, cookies=get_dict_cookies_from_file(),
            )
        resp.encoding = "utf-8"
        resp_is_empty = len(resp.text.strip()) == 0
        resp_json = json.loads(resp.text)
        # Path(f"./aweme_list_2.json").write_text(json.dumps(resp, indent=2,ensure_ascii=False), encoding='utf8')
        return resp_json
    except Exception as e:
        logger.error(f'获取抖音用户动态失败，可能是cookie 或 X-Bogus失效: {e} id:{name}, empty resp:{resp_is_empty}')
        return None

async def get_aweme_short_url(aweme_id) -> Optional[str]:
    """获取视频短链"""
    url = (f"https://www.douyin.com/aweme/v1/web/web_shorten/?target=https://www.iesdouyin.com/share/video/{aweme_id}/"
            + "?region=CN&from=web_code_link&belong=aweme&persist=1&device_platform=webapp&aid=6383&channel=channel_pc_web"
            + REQ_SUFFIX)
    url = add_xbogus(url)

    headers = {
        'referer': f"https://www.douyin.com/video/{aweme_id}",
        'User-Agent': USER_AGENT
    }

    try:
        async with AsyncClient() as client:
            resp = await client.get(
                url, headers=headers,
            )
        resp.encoding = "utf-8"
        resp_json = json.loads(resp.text)
        if 'data' not in resp_json:
            logger.error(f"获取视频短链失败，: {resp_json['reason']}")
            return None
        else:
            return resp_json['data']
    except Exception as e:
        logger.error(f'获取视频短链失败，可能是 X-Bogus 算法已过时: {e}')
        return None
    
_js_compiled = None
def add_xbogus(url:str) -> str:
    """给url添加 X-Bogus 参数"""
    global _js_compiled
    if not _js_compiled:    
        js_path = f"{Path(__file__).parent}/X-Bogus.js"
        _js_compiled = execjs.compile(open(js_path).read())

    query = urllib.parse.urlparse(url).query
    xbogus = _js_compiled.call('sign', query, USER_AGENT)
    url = url + "&X-Bogus=" + xbogus
    return url

async def create_aweme_msg(dyn:Any) -> Message:
    """生成作品消息"""
    aweme_id = dyn["aweme_id"]
    create_time = datetime.fromtimestamp(int(dyn["create_time"]))
    nickname = dyn["author"]["nickname"]
    cover_url = dyn["video"]["cover"]["url_list"][0]
    share_url = dyn["share_url"]
    share_info = dyn["share_info"] # share_url, share_link_desc
    region = dyn["region"]
    duration = dyn["duration"]
    statics = dyn["statistics"] # comment_count, digg_count, collect_count
    allow_share = dyn["status"]["allow_share"]

    msg: Message = MessageSegment.image(cover_url) + f"\n{nickname} 于 {create_time} 发布了作品\n--------------------\n"

    short_url = await get_aweme_short_url(aweme_id)
    if short_url:
        return msg + f"{share_info['share_link_desc'] % short_url}"
    else:
        video_url = f"https://www.douyin.com/video/{aweme_id}"
        return msg + video_url

async def create_live_msg(user: User_dy, room_info: RoomInfo) -> Message:
    """生成直播分享x信息"""
    # https://live.douyin.com/824433208053?room_id=7282413254901533479&enter_from_merge=web_share_link&enter_method=web_share_link&previous_page=app_code_link
    # 1- #在抖音，记录美好生活#【一吱大仙】正在直播，来和我一起支持Ta吧。复制下方链接，打开【抖音】，直接观看直播！ https://v.douyin.com/ieGsnGsm/ 8@5.com 02/11

    title = room_info.get_title()
    cover = room_info.get_cover_url()

    if user.live_url:
        share_msg = (f"\n{random.randint(1, 9)}- #在抖音，记录美好生活#【{user.name}】正在直播，来和我一起支持Ta吧。复制下方链接，打开【抖音】，直接观看直播！ {user.live_url}"
                     f" {random.randint(1, 9)}@{random.randint(1, 9)}.com {random.randint(1, 11):02}/{random.randint(1, 11):02}")
    else:
        share_msg = f"https://live.douyin.com/{user.room_id}"

    live_msg = (
        f"{user.name} 正在直播\n--------------------\n标题：{title}\n" + MessageSegment.image(cover) + f"\n{share_msg}"
    )
    return live_msg

async def get_room_id_and_sec_uid_from_live_url(live_url: str) -> Tuple[int, str]:
    """通过直播间短链获取直播间号和 sec_uid"""
    room_id,sec_user_id = await get_sec_user_id_from_live_url(live_url)
    web_rid = await get_live_room_id(room_id,sec_user_id)
    return (web_rid, sec_user_id)