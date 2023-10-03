import asyncio
import os
import re
import sys
import json
from pathlib import Path
from typing import Any, List, Dict, Optional
from pydantic import BaseSettings
from bilireq.auth import Auth
from nonebot.log import logger
from . import config

class BiliAuth(BaseSettings):
    """Bilibili用户认证相关数据，其中cookie有两种来源，分别从Auth和浏览器获取"""
    auth: Optional[Auth]
    is_logined:bool

    def set_auth(self, auth:Auth):
        self.auth = auth
        self.is_logined = auth != None

    def remove_auth(self):
        self.auth = None
        self.is_logined = False

    def get_list_auth_cookies(self, domain:str = ".bilibili.com") -> List[Any]:
        """获取token auth的list类型的cookie数据"""
        cookies_raw = self.auth["origin"]["cookie_info"]["cookies"] if self.auth else list()
        cookies = [{ "name":ck["name"], "value":ck["value"], "path":"/", "domain": domain }
                        for ck in cookies_raw]
        return cookies
    
    def get_dict_auth_cookies(self) -> Dict[str, Any]:
        """获取token auth的dict格式的cookie"""
        return self.auth.cookies if self.auth else dict()
        
    def get_list_cookies_from_file(self) -> List[Any]:
        """从文件读取浏览器cookie"""
        cookies = list()
        if not config.haruka_cookie_file:
            logger.error("无法从文件加载cookie, 没有配置浏览器cookie文件路径")
            return cookies
        
        try:
            cookies_raw = json.loads(Path(config.haruka_cookie_file).read_text("utf-8"))  # type: ignore
            cookies = [{ "name":ck["name"], "value":ck["value"], "path":ck["path"], "domain": ck["domain"] }
                        for ck in cookies_raw]
        except Exception as e:
            logger.error(f"读取cookie文件失败:{e}")

        return cookies
    
    def get_dict_cookies_from_file(self) -> Dict[str, Any]:
        """从文件读取浏览器cookie并转换为dict格式"""
        cookie_list = self.get_list_cookies_from_file()
        return {ck["name"]:ck["value"] for ck in cookie_list}
    
    def get_list_cookies(self) -> List[Any]:
        """获取list格式的cookie, 首先尝试从文件读取，不存在时再尝试获取auth中的cookie"""
        cookies = self.get_list_cookies_from_file()
        if len(cookies) == 0:
            cookies = self.get_list_auth_cookies()
        return cookies
    
    def get_dict_cookies(self) -> Dict[str, Any]:
        """获取dict格式的cookie, 首先尝试从文件读取，不存在时再尝试获取auth中的cookie"""
        cookies = self.get_dict_cookies_from_file()
        if len(cookies) == 0:
            cookies = self.get_dict_auth_cookies()
        return cookies
    
    def save_cookies_to_file(self, cookies: List[Any]):
        """保存浏览器cookie到文件"""
        if not config.haruka_cookie_file:
            logger.error("无法将cookie写入文件, 没有配置浏览器cookie文件路径")
            return
        Path(config.haruka_cookie_file).write_text(json.dumps(cookies, indent=2,ensure_ascii=False))

bili_auth = BiliAuth(auth=None, is_logined=False)
