import re
import secrets

from nonebot import get_driver
from nonebot.typing import T_State
from loguru import logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment, Message
from nonebot.plugin import on_regex

from githubkit import GitHub, Response
from githubkit.rest import FullRepository

from ..utils import get_github_screenshot

GITHUB_URL_REGEX_PATTERN = r"(?:https://)?github\.com/([^/]+)/([^/\s]+)(/[^\s]+)?"

github = GitHub(get_driver().config.__dict__.get('github_token', None))

on_github = on_regex(GITHUB_URL_REGEX_PATTERN, priority=10, block=False)
# on_github.__doc__ = "发送 github 卡片"
    
@on_github.handle()
async def github_handle(bot: Bot, event: GroupMessageEvent, state: T_State):
    match = re.search(GITHUB_URL_REGEX_PATTERN, event.get_plaintext())
    if match:
        user = match.group(1)
        repo = match.group(2)
        params = match.group(3) or ''

        if re.search('^(/issues/|/pull/|/blob/)', params):
            msg = MessageSegment.image(await get_github_screenshot(f'https://github.com/{user}/{repo}{params}'))
        else:
            msg = MessageSegment.image(f"https://opengraph.githubassets.com/{secrets.token_urlsafe(16)}/{user}/{repo}{params}")
        await on_github.send(msg)
    else:
        return
