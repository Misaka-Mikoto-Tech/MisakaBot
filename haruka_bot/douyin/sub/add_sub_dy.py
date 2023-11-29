import re
from datetime import datetime
from typing import List
from loguru import logger
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent
from nonebot.internal.matcher import Matcher, current_event
from nonebot.params import ArgPlainText, CommandArg

from ...database import DB as db
from ...utils import on_command, to_me, permission_check, text_to_img
from ..utils_dy import get_user_dynamics, get_sec_user_id, get_aweme_short_url, create_aweme_msg, get_room_id_and_sec_uid_from_live_url
from ... import config

add_sub_dy = on_command("抖音关注", aliases={"关注抖音", "抖音订阅"}, rule=to_me(), priority=5, block=True)
add_sub_dy.__doc__ = """抖音关注 用户名"""

add_sub_dy.handle()(permission_check)

@add_sub_dy.handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, arg: Message = CommandArg()
):
    if arg.extract_plain_text().strip():
        matcher.set_arg("user_name", arg)

kLiveShareTips = ('● 请发送以下任意内容：\n'
                  '   1.直播间分享[推荐]（手机端打开直播间，右下角 分享->复制链接）\n'
                  '   2.直播间号\n'
                  '● 忽略直播请发送 N')

@add_sub_dy.got("user_name", "请发送抖音用户名")
@add_sub_dy.got("live_url", kLiveShareTips)
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot
    , user_name: str = ArgPlainText("user_name")
    , live_url: str = ArgPlainText("live_url")
):
    user_name = user_name.strip()
    live_url = live_url.strip()

    is_short_url: bool = False
    room_id = 0

    if live_url.upper() == 'N':
        live_url = ''
    elif live_url.isdigit():
        room_id = live_url
        live_url = f'https://live.douyin.com/{live_url}'
    else:
        url_match = re.search(r'(https://v.douyin.com/\w+/)', live_url)
        if not url_match:
            await matcher.reject('直播间订阅数据有误，请重新输入, 忽略请发送N')
        else:
            live_url = url_match.group(1)
            is_short_url = True

    if is_short_url: # 存在直播间短链的情况下，优先使用从短链获取的数据（抖音允许重名，短链分享不会获取到重名用户）
        room_id, sec_uid = await get_room_id_and_sec_uid_from_live_url(live_url)
        if room_id == 0:
            await matcher.finish(f'获取room_id失败，请确保复制的是分享链接而不是分享到QQ')
    else:
        if not (sec_uid := await get_sec_user_id(user_name=user_name)):
            return await add_sub_dy.send(MessageSegment.at(event.user_id) + " 未找到该抖音用户名")

        if isinstance(sec_uid, list):
            return await add_sub_dy.send(MessageSegment.at(event.user_id) + f" 未找到{user_name}, 你是否想要找:\n" + '\n'.join([item['user_info']['nickname'] for item in sec_uid[:10] ]))
    
    room_str = f"({room_id})" if room_id != 0 else ''
    
    result_exists = await db.get_sub_dy(group_id=event.group_id,
        bot_id=int(bot.self_id),
        sec_uid=sec_uid)
    
    if result_exists:
        await db.update_sub_dy(name=user_name,
            group_id=event.group_id,
            bot_id=int(bot.self_id),
            sec_uid=sec_uid,
            room_id=room_id,
            live_url=live_url)

        await add_sub_dy.finish(f"已更新抖音用户 {user_name}{room_str}")
    else:
        result = await db.add_sub_dy(
            name=user_name,
            group_id=event.group_id,
            bot_id=int(bot.self_id),
            sec_uid=sec_uid,
            room_id=room_id,
            live_url=live_url
        )
        if result:
            await add_sub_dy.finish(f"已关注抖音用户 {user_name}{room_str}")
        await add_sub_dy.finish(f"{user_name}{room_str} 已经关注了")