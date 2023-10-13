
import json
import asyncio
from pathlib import Path
from typing import List
from loguru import logger
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.internal.matcher import Matcher, current_event
from nonebot.params import ArgPlainText, CommandArg
# from bilireq.grpc.dynamic import grpc_get_user_dynamics
# from bilireq.grpc.protos.bilibili.app.dynamic.v2.dynamic_pb2 import DynamicType

from ..utils import on_command, to_me, text_to_img
from ..utils.uid_extract import uid_extract
from ..utils.bilibili_request import get_b23_url
from ..utils import get_dynamic_screenshot, get_user_dynamics
from ..bili_auth import bili_auth
from .. import config

vive = on_command("查看动态", aliases={"查询动态"}, rule=to_me(), priority=5, block=True) # 数值越小优先级越高
vive.__doc__ = "查看动态"

@vive.handle()
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg_msg: Message = CommandArg()
):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)

@vive.got("arg", "请发送UP名称")
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg: str = ArgPlainText("arg")
):
    vive_texts = arg.strip().split(' ')
    logger.info(f"接收到查询数据:{vive_texts}")

    # if not bili_auth.is_logined:
    #     await vive.finish("未登录B站账号，请先登录")

    name = vive_texts[0]
    if not (uid := await uid_extract(name)):
        return await vive.send(MessageSegment.at(event.user_id) + " 未找到该 UP，请输入正确的UP 名、UP UID或 UP 首页链接")

    if isinstance(uid, list):
        return await vive.send(MessageSegment.at(event.user_id) + f" 未找到{name}, 你是否想要找:\n" + '\n'.join([item['uname'] for item in uid[:10] ]))
    elif int(uid) == 0:
        return await vive.send(MessageSegment.at(event.user_id) + " UP 主不存在")

    user_agent: str = config.haruka_browser_ua or (
            "Mozilla/5.0 (Linux; Android 11; RMX3161 Build/RKQ1.201217.003; wv) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Version/4.0 Chrome/101.0.4896.59 Mobile Safari/537.36")
    
    try:
        # logger.info(f"B站Token:{bili_auth.auth}")
        # res = await grpc_get_user_dynamics(int(uid), auth=bili_auth.auth)
        dynamics = (await get_user_dynamics(
            int(uid), 
            cookies=bili_auth.get_dict_auth_cookies(),
            ua=user_agent,
            timeout=config.haruka_dynamic_timeout,
            proxies=config.haruka_proxy
            )
            )["items"]
    except Exception as e:
        return await vive.send(MessageSegment.at(event.user_id) + f" 获取动态失败：{e}")

    offset_num = int(vive_texts[1]) if len(vive_texts) > 1 else 0

    if dynamics:
        dynamics = sorted(dynamics, key=lambda x: int(x["id_str"]), reverse=True)
        # Path('./bili_dynamics.json').write_text(json.dumps(dynamics, indent=2,ensure_ascii=False))
        # logger.info(f"动态列表:{dynamics}, offset_num:{offset_num}")
        try:
            dyn = dynamics[offset_num]
        except IndexError:
            return await vive.send(MessageSegment.at(event.user_id) + " 你输入的数字过大，该 UP 的最后一页动态没有这么多条")
        dynamic_id = int(dyn["id_str"])
        shot_image = await get_dynamic_screenshot(dynamic_id)
        if shot_image is None:
            return await vive.send(MessageSegment.at(event.user_id) + f" 获取{name}动态失败")
        type_msg = {
                0: "发布了新动态",
                "DYNAMIC_TYPE_FORWARD": "转发了一条动态",
                "DYNAMIC_TYPE_WORD": "发布了新文字动态",
                "DYNAMIC_TYPE_DRAW": "发布了新图文动态",
                "DYNAMIC_TYPE_AV": "发布了新投稿",
                "DYNAMIC_TYPE_ARTICLE": "发布了新专栏",
                "DYNAMIC_TYPE_MUSIC": "发布了新音频",
            }
        
        if dyn['type'] == 'DYNAMIC_TYPE_AV':  # 视频动态直接放视频链接，动态里的视频框在App上视频点不动（可能是B站bug）
            jump_url: str = dyn['modules']['module_dynamic']['major']['archive']['jump_url']
            BV = jump_url[len('//www.bilibili.com/video/'):-1]
            jump_url = f'https://b23.tv/{BV}'
        else:
            jump_url = await get_b23_url(f"https://t.bilibili.com/{dynamic_id}")

        message = (
            MessageSegment.at(event.user_id)
            + f" {name} {type_msg.get(dyn['type'], type_msg[0])}：\n"
            + MessageSegment.image(shot_image)
            + f"\n"
            + jump_url
        )

        return await vive.send(message)
        
    return await vive.send("该 UP 未发布任何动态")
