import asyncio
import os
import re
import sys
import json
from nonebot.log import logger
from typing import List, Dict, Optional, Any
from pathlib import Path
from pydantic import BaseSettings, validator
from pydantic.fields import ModelField


# 其他地方出现的类似 from .. import config，均是从 __init__.py 导入的 Config 实例
class Config(BaseSettings):
    fastapi_reload: bool = False
    haruka_dir: Optional[str] = None
    haruka_to_me: bool = True
    haruka_live_off_notify: bool = False
    haruka_proxy: Optional[str] = None
    haruka_interval: int = 10
    haruka_live_interval: int = haruka_interval
    haruka_dynamic_interval: int = 0
    haruka_dynamic_at: bool = False
    haruka_screenshot_style: str = "mobile"
    haruka_dynamic_timeout: int = 10
    haruka_dynamic_font_source: str = "system"
    haruka_dynamic_font: Optional[str] = "Noto Sans CJK SC"
    haruka_command_prefix: str = ""
    haruka_browser_ua:  Optional[str] = None
    haruka_cookie_file: Optional[str] = None
    haruka_login_cache_file: str = "./login_cache.json"
    # 频道管理员身份组
    haruka_guild_admin_roles: List[str] = ["频道主", "超级管理员"]
    exclusive_bots:List[int] = [] # 独占模式的bot列表，只允许自己控制自己
    super_user_mode_bots:List[int] = [] # 默认超管和普通管理员都可以控制的操作，改为只允许超管, 优先级低于exclusive_bots
    bot_names:Dict[int,str] = {}
    overseas_proxy: Optional[str] = None # 海外业务使用的代理

    @validator("haruka_interval", "haruka_live_interval", "haruka_dynamic_interval")
    def non_negative(cls, v: int, field: ModelField):
        """定时器为负返回默认值"""
        if v < 1:
            return field.default
        return v

    class Config:
        extra = "ignore"
