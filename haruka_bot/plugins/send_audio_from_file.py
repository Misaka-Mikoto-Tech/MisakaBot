
import json
import asyncio
import re
from pathlib import Path
from typing import List, Tuple
from loguru import logger
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent
from nonebot.internal.matcher import Matcher, current_event
from nonebot.params import ArgPlainText, CommandArg

from ..utils import on_command, to_me, text_to_img
from ..utils.uid_extract import uid_extract
from ..utils.bilibili_request import get_b23_url
from ..utils import get_dynamic_screenshot, get_user_dynamics
from ..bili_auth import bili_auth
from .. import config

send_wav = on_command("发送语音文件", aliases={"发送wav"}, rule=to_me(), priority=5, block=True) # 数值越小优先级越高
# send_wav.__doc__ = "发送语音文件 group wav_path"

@send_wav.handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot:Bot, arg: Message = CommandArg()
):
    text = arg.extract_plain_text().strip()
    if not text:
        return await send_wav.finish("未发送参数")
    
    # 命令格式 group wav_path
    match = re.match(r'(\d+)\s+(.+\.wav)', text)
    if match:
        group_id = int(match.group(1))
        wav_path = match.group(2)
        wav_path = f'./data/record/{wav_path}'
    else:
        return await send_wav.finish("参数格式错误:group wav_path")
    
    if group_id <= 0:
        group_id = event.group_id

    if not Path(wav_path).exists():
        return await send_wav.finish("wav文件不存在")
    
    silk_path = await get_silk_from_wav(wav_path)
    record_path = silk_path if silk_path else wav_path
    record_path = 'file://' + str(Path(record_path).absolute())

    logger.info(f"发送语音文件: {record_path} 到群: {group_id}")

    msg: Message = Message(MessageSegment.record(record_path))
    await bot.send_group_msg(group_id=group_id, message= msg)

    await asyncio.sleep(5) # 5秒后删除临时文件
    if Path(silk_path).exists():
        Path(silk_path).unlink()

async def get_silk_from_wav(wav_path: str) -> str:
    """尝试将wav转换成silk文件"""
    silk_path = wav_path.replace('.wav', '.silk')
    if Path(silk_path).exists():
        return silk_path
    
    p = await asyncio.create_subprocess_exec('./bin/wav2silk.sh', wav_path)
    output = await p.communicate()
    output0 = output[0].decode('utf-8')
    output1 = output[1].decode('utf-8')
    if output0:
        logger.info(output0)
    if output1:
        logger.error(output1)

    if Path(silk_path).exists():
        return silk_path
    else:
        return ""