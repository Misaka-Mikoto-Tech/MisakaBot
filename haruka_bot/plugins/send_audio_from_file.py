
# import json
# import asyncio
# from pathlib import Path
# from typing import List, Tuple
# from loguru import logger
# from nonebot.matcher import matchers
# from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
# from nonebot.adapters.onebot.v11.event import MessageEvent
# from nonebot.internal.matcher import Matcher, current_event
# from nonebot.params import ArgPlainText, CommandArg

# from ..utils import on_command, to_me, text_to_img
# from ..utils.uid_extract import uid_extract
# from ..utils.bilibili_request import get_b23_url
# from ..utils import get_dynamic_screenshot, get_user_dynamics
# from ..bili_auth import bili_auth
# from .. import config

# send_wav = on_command("发送语音文件", aliases={"发送wav"}, rule=to_me(), priority=5, block=True) # 数值越小优先级越高
# # vive.__doc__ = "发送语音文件 group wav_path"

# @send_wav.handle()
# async def _(
#     matcher: Matcher, event: MessageEvent, bot:Bot, arg_msg: Message = CommandArg()
# ):
#     if arg_msg.extract_plain_text().strip():
#         matcher.set_arg("arg", arg_msg)

# @send_wav.got("arg", "请发送UP名称")
# async def _(
#     matcher: Matcher, event: MessageEvent, bot:Bot, arg: str = ArgPlainText("arg")
# ):
#     vive_text = arg.strip()
#     logger.info(f"接收到查询数据:{vive_text}")

#     user_name, v_mode, offset_num = parseArgs(vive_text)

#     if not (uid := await uid_extract(user_name)):
#         return await send_wav.send(MessageSegment.at(event.user_id) + " 未找到该 UP，请输入正确的UP 名、UP UID或 UP 首页链接")

#     if isinstance(uid, list):
#         return await send_wav.send(MessageSegment.at(event.user_id) + f" 未找到 {user_name}, 你是否想要找:\n" + '\n'.join([item['uname'] for item in uid[:10] ]))
#     elif int(uid) == 0:
#         return await send_wav.send(MessageSegment.at(event.user_id) + " UP 主不存在")

#     user_agent: str = config.haruka_browser_ua or (
#             "Mozilla/5.0 (Linux; Android 11; RMX3161 Build/RKQ1.201217.003; wv) AppleWebKit/537.36 "
#          "(KHTML, like Gecko) Version/4.0 Chrome/101.0.4896.59 Mobile Safari/537.36")
    
#     try:
#         # logger.info(f"B站Token:{bili_auth.auth}")
#         # res = await grpc_get_user_dynamics(int(uid), auth=bili_auth.auth)
#         dynamics = (await get_user_dynamics(
#             int(uid), 
#             cookies=bili_auth.get_dict_auth_cookies(),
#             ua=user_agent,
#             timeout=config.haruka_dynamic_timeout,
#             proxies=config.haruka_proxy
#             )
#             )["items"]
#     except Exception as e:
#         return await send_wav.send(MessageSegment.at(event.user_id) + f" 获取动态失败：{e}")

#     if dynamics:
#         dynamics = sorted(dynamics, key=lambda x: int(x["id_str"]), reverse=True)
#         if v_mode: # 只查看视频
#             dynamics = [dyn for dyn in dynamics if dyn['type'] == 'DYNAMIC_TYPE_AV']
#         # Path('./bili_dynamics.json').write_text(json.dumps(dynamics, indent=2,ensure_ascii=False))
#         # logger.info(f"动态列表:{dynamics}, offset_num:{offset_num}")
#         try:
#             dyn = dynamics[offset_num]
#         except IndexError:
#             return await send_wav.send(MessageSegment.at(event.user_id) + " 你输入的数字过大，该 UP 的最后一页动态没有这么多条")
#         dynamic_id = int(dyn["id_str"])
#         shot_image = await get_dynamic_screenshot(dynamic_id)
#         if shot_image is None:
#             return await send_wav.send(MessageSegment.at(event.user_id) + f" 获取{user_name}动态失败")
#         type_msg = {
#                 0: "发布了新动态",
#                 "DYNAMIC_TYPE_FORWARD": "转发了一条动态",
#                 "DYNAMIC_TYPE_WORD": "发布了新文字动态",
#                 "DYNAMIC_TYPE_DRAW": "发布了新图文动态",
#                 "DYNAMIC_TYPE_AV": "发布了新投稿",
#                 "DYNAMIC_TYPE_ARTICLE": "发布了新专栏",
#                 "DYNAMIC_TYPE_MUSIC": "发布了新音频",
#             }
        
#         if dyn['type'] == 'DYNAMIC_TYPE_AV':  # 视频动态直接放视频链接，动态里的视频框在App上视频点不动（可能是B站bug）
#             jump_url: str = dyn['modules']['module_dynamic']['major']['archive']['jump_url']
#             BV = jump_url[len('//www.bilibili.com/video/'):-1]
#             jump_url = f'https://b23.tv/{BV}'
#         else:
#             jump_url = await get_b23_url(f"https://t.bilibili.com/{dynamic_id}")

#         message = (
#             f" {user_name} {type_msg.get(dyn['type'], type_msg[0])}：\n"
#             + MessageSegment.image(shot_image)
#             + f"\n"
#             + jump_url
#         )

#         return await send_wav.send(message)
        
#     return await send_wav.send("该 UP 未发布任何动态")

# def parseArgs(text:str)->Tuple[str, bool, int]:
#     """从参数解析出 user_name, v_mode, offset"""
#     args = text.split(' ')
#     argc = len(args)

#     # B站用户名不允许包含空格，因此可以从前往后解析
#     user_name = args[0]
#     v_mode = False
#     offset_num = 0

#     if argc > 1:
#         arg1 = args[1]
#         if arg1 == 'v':
#             v_mode = True
#             if argc > 2:
#                 arg2 = args[2]
#                 if arg2.isdigit():
#                     offset_num = int(arg2)
#         elif arg1.isdigit():
#             offset_num = int(arg1)

#     return (user_name, v_mode, offset_num)