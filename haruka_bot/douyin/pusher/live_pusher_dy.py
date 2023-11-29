import asyncio
import random
import time
from pathlib import Path
from typing import Dict, Tuple
from dataclasses import dataclass, astuple

from nonebot.log import logger

from nonebot.adapters.onebot.v11.message import MessageSegment, Message

from ...utils import scheduler, safe_send
from ...database import DB as db

from ..core import dy_api
from ..core.room_info import RoomInfo
from ..utils_dy import cookie_utils
from ...database.models import User_dy

# users = [{"name":"一千夏🥥", "sec_user_id":"MS4wLjABAAAALUW2eoJvmC2Q29Qhv82Db8S8V6dWMczwQfqEc1-XFaS2yxMn7oGFcJHnTkOUZAzC", "room_id": 65276150732}]

@dataclass
class LiveStatusData:
    """直播间状态数据"""
    user_name:str
    is_streaming:bool = False # 是否在直播
    online_time:float = 0
    offline_time:float = 0

all_status:Dict[str,LiveStatusData] = {} # [sec_user_id, LiveStatusData]

def format_time_span(seconds:float)->str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h)}小时{int(m)}分"
    
@scheduler.scheduled_job("interval", seconds=6, id="live_sched_dy")
async def live_sched_dy():
    """dy直播推送"""

    sec_uid: str = str(await db.next_uid_dy("live"))
    if not sec_uid: # 未找到
        # 没有订阅先暂停一秒再跳过，不然会导致 CPU 占用过高
        await asyncio.sleep(1)
        return

    user = await db.get_user_dy(sec_uid=sec_uid)
    if not user:
        # logger.error(f'没找到抖音用户{sec_uid}')
        return

    logger.debug(f"获取抖音直播状态 {user.name}（{sec_uid}）")
    await cookie_utils.get_cookie_cache()

    room_json = await dy_api.get_live_state_json(user.room_id)
    # Path(f"./dy_live_info.json").write_text(json.dumps(room_json, indent=2,ensure_ascii=False), encoding='utf8')
    if room_json is None:
        await cookie_utils.record_cookie_failed()
        return
    room_info = RoomInfo(room_json)
    
    new_status = await room_info.is_going_on_live()
    if sec_uid not in all_status:
        # bot 开启时正在直播的将bot启动时间设置为开播时间
        all_status[sec_uid] = LiveStatusData(user.name, new_status, time.time() if new_status else 0)
        return
    
    status_data = all_status[sec_uid] 
    old_status = status_data.is_streaming
    if new_status == old_status:  # 直播间状态无变化
        return
    status_data.is_streaming = new_status

    if new_status:  # 开播
        status_data.online_time = time.time()
        logger.info(f'检测到抖音 {user.name}({user.room_id}) 开播。标题:{room_info.get_title()}')
        live_msg, link_msg = create_live_msg(user, room_info)
    else:  # 下播
        status_data.offline_time = time.time()
        online_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(status_data.online_time))
        logger.info(f"检测到抖音下播：{user.name}({user.room_id}), 开播时间:{online_time_str}")

        if status_data.online_time > 0:
            live_msg = f"{user.name} 抖音下播了\n本次直播时长 {format_time_span(status_data.offline_time - status_data.online_time)}"
        else:
            live_msg = f"{user.name} 抖音下播了"
        link_msg = ''

    # 推送
    push_list = await db.get_push_list_dy(sec_uid)
    for sets in push_list:
        # 先尝试整体发送
        send_ret = await safe_send(
            bot_id=sets.bot_id,
            send_type='group',
            type_id=sets.group_id,
            message=f'{live_msg}\n{link_msg}',
            at=bool(sets.at) if new_status else False,  # 下播不@全体
            prefix=f'{random.randint(1, 9)} ' if new_status else None, # ios 要求第一个字符必须是数字才允许app读取剪贴板
        )

        # 发送失败时再尝试分片发送 (tx对抖音直播链接有风控，开播消息分成两条发送成功率更高)
        if not(send_ret and send_ret.get('message_id', '0') != '0'):
            await safe_send(
                bot_id=sets.bot_id,
                send_type='group',
                type_id=sets.group_id,
                message=live_msg,
                at=bool(sets.at) if new_status else False,  # 下播不@全体
            )
            await asyncio.sleep(0.5)

            if link_msg:
                await safe_send(
                    bot_id=sets.bot_id,
                    send_type='group',
                    type_id=sets.group_id,
                    message=f'{user.name} 直播间链接 {link_msg}',
                    at=False,
                    prefix=f'{random.randint(1, 9)} ', # ios 要求第一个字符必须是数字才允许app读取剪贴板
                )

        await asyncio.sleep(0.5)

def create_live_msg(user: User_dy, room_info: RoomInfo) -> Tuple[Message, Message]:
    """生成直播分享信息"""
    # https://live.douyin.com/824433208053?room_id=7282413254901533479&enter_from_merge=web_share_link&enter_method=web_share_link&previous_page=app_code_link
    # 1- #在抖音，记录美好生活#【一吱大仙】正在直播，来和我一起支持Ta吧。复制下方链接，打开【抖音】，直接观看直播！ https://v.douyin.com/ieGsnGsm/ 8@5.com 02/11

    title = room_info.get_title()
    cover = room_info.get_cover_url()

    live_msg = f"{user.name} 正在直播\n--------------------\n标题：{title}\n" + MessageSegment.image(cover) \
                + f"\n{random.randint(1, 9)}- #在抖音，记录美好生活#【{user.name}】正在直播，来和我一起支持Ta吧。复制下方链接，打开【抖音】，直接观看直播！"

    if user.live_url:
        link_msg = MessageSegment.text(f"{user.live_url}") + ''
    else:
        link_msg = MessageSegment.text(f"https://live.douyin.com/{user.room_id}") + ''

    return (live_msg, link_msg)

@scheduler.scheduled_job("interval", seconds=3.5 * 3600, id="live_sched_dy_auto_get_cookie")
async def live_scheh_dy_auto_get_cookie():
    """dy直播临时cookie定时刷新"""

    await cookie_utils.auto_get_cookie()

