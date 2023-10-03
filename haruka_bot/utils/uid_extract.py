import re

from loguru import logger
from typing import Any, List, Union, Optional

from ..database.db import DB as db
from .b23_extract import b23_extract
from .bilibili_request import search_user
from ..bili_auth import bili_auth


async def uid_extract(text: str)-> Union[Optional[str], List[Any]]:
    if text.strip().isdigit():
        return text.strip()
    
    logger.debug(f"[UID Extract] Original Text: {text}")
    if user_data := await db.get_user(name=text):
        logger.debug(f"[UID Extract] 数据库中找到:{user_data}")
        return str(user_data.uid)

    b23_msg = await b23_extract(text) if "b23.tv" in text else None
    message = b23_msg or text
    logger.debug(f"[UID Extract] b23 extract: {message}")
    pattern = re.compile("^[0-9]*$|bilibili.com/([0-9]*)")
    if match := pattern.search(message):
        logger.debug(f"[UID Extract] Digit or Url: {match}")
        match = match[1] or match[0]
        return str(match)
    elif message.startswith("UID:"):
        pattern = re.compile("^\\d+")
        if match := pattern.search(message[4:]):
            logger.debug(f"[UID Extract] UID: {match}")
            return str(match[0])
    else:
        text_u = text.strip(""""'“”‘’""")
        if text_u != text:
            logger.debug(f"[UID Extract] Text is a Quoted Digit: {text_u}")
        logger.debug(f"[UID Extract] Searching UID in BiliBili: {text_u}")
        resp = await search_user(text_u, cookies=bili_auth.get_dict_auth_cookies())
        logger.debug(f"[UID Extract] Search result: {resp}")
        if resp and resp["numResults"]:
            for result in resp["result"]:
                if result["uname"] == text_u:
                    logger.debug(f"[UID Extract] Found User: {result}")
                    return str(result["mid"])
            return resp["result"]
        logger.debug("[UID Extract] No User found")
    return str("0")