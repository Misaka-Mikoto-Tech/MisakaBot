from typing import List
from nonebot.matcher import matchers
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import MessageEvent

from ..utils import on_command, to_me, text_to_img
from ..version import __version__
from .. import config

help = on_command("帮助", aliases={"help"},  rule=to_me(), priority=5, block=True) # 数值越小优先级越高


@help.handle()
async def _(event: MessageEvent, bot:Bot):
    bot_id = int(bot.self_id)
    if bot_id in config.bot_names:
        message = f"<font color=green><b>{config.bot_names[bot_id]}目前支持的功能：</b></font>\n（[]表示参数为可选）\n"
    else:
        message = "<font color=green><b>Bot目前支持的功能：</b></font>\n（[]表示参数为可选）\n"

    plugin_names:List[str] = []
    for matchers_list in matchers.values():
        for matcher in matchers_list:
            if (
                matcher.plugin_name
                and matcher.plugin_name.startswith("haruka_bot")
                and matcher.__doc__
            ):
                doc = matcher.__doc__
                plugin_names.append(doc)

                func_name = doc[2:]
                open_func = f"开启{func_name}"
                close_func = f"关闭{func_name}"
                if (open_func in plugin_names) and (close_func in plugin_names):
                    plugin_names.remove(open_func)
                    plugin_names.remove(close_func)
                    plugin_names.append(f"开启|关闭{func_name}")

                open_func2 = f"关注{func_name}"
                close_func2 = f"取关{func_name}"
                if (open_func2 in plugin_names) and (close_func2 in plugin_names):
                    plugin_names.remove(open_func2)
                    plugin_names.remove(close_func2)
                    plugin_names.append(f"关注|取关{func_name}")

    message += '\n'.join(plugin_names) + "\n"
    message += "网易点歌\n"
    message += "绘画\n------------------------\n"
    message += "示例：开启动态 123456\n"
    message += "Tips：只发送 \"绘画\" 两个字将显示详细绘画帮助内容\n"
    
    message = MessageSegment.image(await text_to_img(message, width=425))
    message += f"\n当前版本：v{__version__}\n" "https://github.com/Misaka-Mikoto-Tech"
    await help.finish(message)
