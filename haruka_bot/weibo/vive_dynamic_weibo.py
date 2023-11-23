from loguru import logger
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent
from nonebot.internal.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg

from ..utils import on_command, to_me
from .utils_weibo import create_dynamic_msg, get_userinfo, get_user_dynamics, search_weibo_user

vive_weibo = on_command("查看微博", aliases={"查询微博", "微博动态"}, rule=to_me(), priority=5, block=True) # 数值越小优先级越高
vive_weibo.__doc__ = "查看微博"

@vive_weibo.handle()
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg_msg: Message = CommandArg()
):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)

@vive_weibo.got("arg", "请发送微博用户名")
async def _(
    matcher: Matcher, event: MessageEvent, bot:Bot, arg: str = ArgPlainText("arg")
):
    vive_text = arg.strip()
    logger.info(f"接收到微博查询数据:{vive_text}")

    args = vive_text.split(' ')
    if args[-1].isdigit():
        user_name = vive_text[:vive_text.rfind(' ')].strip()
        offset_num = int(args[-1])
    else:
        user_name = vive_text
        offset_num = 0

    search_resp = await search_weibo_user(user_name)
    if not search_resp:
        return await vive_weibo.send(MessageSegment.at(event.user_id) + " 未找到该微博用户，请输入正确的用户名")

    if isinstance(search_resp, list):
        return await vive_weibo.send(MessageSegment.at(event.user_id) + f"未找到用户 {user_name}, 你是否想要找:\n" + '\n'.join(search_resp))

    try:
        user_info = await get_userinfo(uid=search_resp.uid)
    except Exception as e:
        await matcher.finish(f"获取微博用户出错，{e.args}")

    try:
        dynamics = await get_user_dynamics(user_info.containerid)
        if dynamics is None:
            return
    except Exception as e:
        logger.error(f"获取微博用户动态失败, {e.args}")
        return
    
    dynamic_list = dynamics['data']['cards'] if "cards" in dynamics['data'] else None
    if not dynamic_list:
        logger.debug(f'用户 {user_info.user_name} 未发布任何微博')
        return
    
    dynamic_list = [dyn for dyn in dynamic_list if dyn['card_type'] == 9] # 暂时不知道其它类型是什么意思
    dynamic_list = sorted(dynamic_list, key=lambda x: int(x["mblog"]["id"]), reverse=True)

    try:
        dyn = dynamic_list[offset_num]
    except IndexError:
        return await vive_weibo.send(MessageSegment.at(event.user_id) + " 你输入的数字过大，该用户的最后一页动态没有这么多条")
    
    await matcher.send(MessageSegment.at(event.user_id) + ' ' + await create_dynamic_msg(dyn))

