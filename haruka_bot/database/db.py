import json
from pathlib import Path
from typing import Dict, List, Optional

from nonebot import get_driver
from nonebot.log import logger
from packaging.version import Version as version_parser
from tortoise import Tortoise
from tortoise.connection import connections

from ..utils import get_path
from ..version import VERSION as HBVERSION
from .models import Group, Guild, Sub, Sub_dy, User, User_dy, Version

uid_list = {"live": {"list": [], "index": 0}, "dynamic": {"list": [], "index": 0}}
dynamic_offset = {} # {uid:latest_dynamic_id}

uid_list_dy = {"live": {"list": [], "index": 0}, "dynamic": {"list": [], "index": 0}} # list: [sec_uid}]
dynamic_offset_dy = {} # {sec_id:latest_dynamic_id}


class DB:
    """数据库交互类，与增删改查无关的部分不应该在这里面实现"""

    @classmethod
    async def init(cls):
        """初始化数据库"""
        config = {
            "connections": {
                "haruka_bot": {
                    "engine": "tortoise.backends.sqlite",
                    "credentials": {
                            "file_path": get_path("data.sqlite3"),
                            "journal_mode":"DELETE"
                        },
                },
                # "haruka_bot": f"sqlite://{get_path('data.sqlite3')}",
            },
            "apps": {
                "haruka_bot_app": {
                    "models": ["haruka_bot.database.models"],
                    "default_connection": "haruka_bot",
                }
            },
        }

        await Tortoise.init(config)

        await Tortoise.generate_schemas()
        await cls.migrate()
        await cls.update_uid_list()
        await cls.update_uid_list_dy()

    @classmethod
    async def get_user(cls, **kwargs):
        """获取 UP 主信息"""
        return await User.get(**kwargs).first()
    
    @classmethod
    async def get_user_dy(cls, **kwargs):
        """获取抖音 UP 主信息"""
        return await User_dy.get(**kwargs).first()

    @classmethod
    async def get_name(cls, uid) -> Optional[str]:
        """获取 UP 主昵称"""
        user = await cls.get_user(uid=uid)
        if user:
            return user.name
        return None
    
    @classmethod
    async def get_name_dy(cls, sec_uid) -> Optional[str]:
        """获取 UP 主昵称"""
        user = await cls.get_user_dy(sec_uid=sec_uid)
        if user:
            return user.name
        return None

    @classmethod
    async def add_user(cls, **kwargs):
        """添加 UP 主信息"""
        return await User.add(**kwargs)
    
    @classmethod
    async def add_user_dy(cls, **kwargs):
        """添加抖音 UP 主信息"""
        return await User_dy.add(**kwargs)

    @classmethod
    async def delete_user(cls, uid) -> bool:
        """删除 UP 主信息"""
        if await cls.get_sub(uid=uid):
            # 还存在该 UP 主订阅，不能删除
            return False
        await User.delete(uid=uid)
        return True
    
    @classmethod
    async def delete_user_dy(cls, sec_uid) -> bool:
        """删除抖音 UP 主信息"""
        if await cls.get_sub_dy(sec_uid=sec_uid):
            # 还存在该抖音 UP 主订阅，不能删除
            return False
        await User_dy.delete(sec_uid=sec_uid)
        return True

    @classmethod
    async def update_user(cls, uid: int, name: str) -> bool:
        """更新 UP 主信息"""
        if await cls.get_user(uid=uid):
            await User.update({"uid": uid}, name=name)
            return True
        return False
    
    @classmethod
    async def update_user_dy(cls, sec_uid: str, name: str) -> bool:
        """更新抖音 UP 主信息"""
        if await cls.get_user_dy(sec_uid=sec_uid):
            await User_dy.update({"sec_uid": sec_uid}, name=name)
            return True
        return False

    @classmethod
    async def get_group(cls, **kwargs):
        """获取群设置"""
        return await Group.get(**kwargs).first()

    @classmethod
    async def get_group_admin(cls, group_id, bot_id) -> bool:
        """获取指定群权限状态"""
        group = await cls.get_group(group_id=group_id, bot_id=bot_id)
        if not group:
            # TODO 自定义默认状态
            return False
        return bool(group.admin)

    @classmethod
    async def get_guild_admin(cls, guild_id, channel_id, bot_id) -> bool:
        """获取指定频道权限状态"""
        guild = await cls.get_guild(guild_id=guild_id, channel_id=channel_id, bot_id=bot_id)
        if not guild:
            # TODO 自定义默认状态
            return False
        return bool(guild.admin)

    @classmethod
    async def get_group_decrease_notice(cls, group_id, bot_id) -> bool:
        """获取指定群退群通知状态"""
        group = await cls.get_group(group_id=group_id, bot_id=bot_id)
        if not group:
            # TODO 自定义默认状态
            return False
        return bool(group.decrease_notice)

    @classmethod
    async def get_guild_decrease_notice(cls, guild_id, channel_id, bot_id) -> bool:
        """获取指定频道退出通知状态"""
        guild = await cls.get_guild(guild_id=guild_id, channel_id=channel_id, bot_id=bot_id)
        if not guild:
            # TODO 自定义默认状态
            return False
        return bool(guild.decrease_notice)
    
    @classmethod
    async def get_group_chatgpt(cls, group_id, bot_id) -> bool:
        """"获取指定群chatgpt开启状态"""
        group = await cls.get_group(group_id=group_id, bot_id=bot_id)
        if not group:
            return False
        return bool(group.chatgpt)
    
    @classmethod
    async def get_guild_chatgpt(cls, guild_id, channel_id, bot_id) -> bool:
        """"获取指定频道chatgpt开启状态"""
        guild = await cls.get_guild(guild_id=guild_id, channel_id=channel_id, bot_id=bot_id)
        if not guild:
            return False
        return bool(guild.chatgpt)
    
    @classmethod
    async def get_group_bili_summary(cls, group_id, bot_id) -> bool:
        """"获取指定群B站视频解析开启状态"""
        group = await cls.get_group(group_id=group_id, bot_id=bot_id)
        if not group:
            return False
        return bool(group.bili_summary)
    
    @classmethod
    async def get_guild_bili_summary(cls, guild_id, channel_id, bot_id) -> bool:
        """"获取指定频道B站视频解析开启状态"""
        guild = await cls.get_guild(guild_id=guild_id, channel_id=channel_id, bot_id=bot_id)
        if not guild:
            return False
        return bool(guild.bili_summary)

    @classmethod
    async def add_group(cls, q=None, **kwargs):
        """创建群设置"""
        return await Group.add(q, **kwargs)

    @classmethod
    async def add_guild(cls, q=None, **kwargs):
        """创建频道设置"""
        return await Guild.add(q, **kwargs)

    @classmethod
    async def delete_guild(cls, guild_id, bot_id) -> bool:
        """删除子频道设置"""
        if await cls.get_sub(type="guild", type_id=guild_id, bot_id=bot_id):
            # 当前频道还有订阅，不能删除
            return False
        await Guild.delete(guild_id=guild_id, bot_id=bot_id)
        return True

    @classmethod
    async def delete_group(cls, group_id, bot_id) -> bool:
        """删除群设置"""
        if await cls.get_sub(type="group", type_id=group_id, bot_id=bot_id):
            # 当前群还有订阅，不能删除
            return False
        await Group.delete(group_id=group_id, bot_id=bot_id)
        return True

    @classmethod
    async def set_group_permission(cls, group_id, bot_id, switch):
        """设置指定群组权限"""
        q = {"group_id": group_id,"bot_id":bot_id}
        if not await cls.add_group(q, **q, admin=switch):
            return await Group.update(q, admin=switch)
        return True

    @classmethod
    async def set_guild_permission(cls, guild_id, channel_id, bot_id, switch):
        """设置指定频道权限"""
        q = {"guild_id": guild_id, "channel_id": channel_id, "bot_id": bot_id}
        if not await cls.add_guild(q, **q, admin=switch):
            return await Guild.update(q, admin=switch)
        return True

    @classmethod
    async def set_group_decrease_notice(cls, group_id, bot_id, switch):
        """设置指定群组退群通知"""
        q = {"group_id": group_id,"bot_id":bot_id}
        if not await cls.add_group(q, **q, decrease_notice=switch):
            return await Group.update(q, decrease_notice=switch)
        return True

    @classmethod
    async def set_guild_decrease_notice(cls, guild_id, channel_id, bot_id, switch):
        """设置指定频道退出通知"""
        q = {"guild_id": guild_id, "channel_id": channel_id, "bot_id": bot_id}
        if not await cls.add_guild(q, **q, decrease_notice=switch):
            return await Guild.update(q, decrease_notice=switch)
        return True

    @classmethod
    async def set_group_chatgpt(cls, group_id, bot_id, switch):
        """设置指定群组chatgpt状态"""
        q = {"group_id":group_id, "bot_id":bot_id}
        if not await cls.add_group(q, **q, chatgpt=switch):
            return await Group.update(q, chatgpt=switch)
        return True

    @classmethod
    async def set_guild_chatgpt(cls, guild_id, channel_id, bot_id, switch):
        """设置指定频道chatgpt状态"""
        q = {"guild_id":guild_id,"channel_id": channel_id, "bot_id":bot_id}
        if not await cls.add_guild(q, **q, chatgpt=switch):
            return await Guild.update(q, chatgpt=switch)
        return True
    
    @classmethod
    async def set_group_bili_summary(cls, group_id, bot_id, switch):
        """设置指定群组B站视频解析状态"""
        q = {"group_id":group_id, "bot_id":bot_id}
        if not await cls.add_group(q, **q, bili_summary=switch):
            return await Group.update(q, bili_summary=switch)
        return True

    @classmethod
    async def set_guild_bili_summary(cls, guild_id, channel_id, bot_id, switch):
        """设置指定频道B站视频解析状态"""
        q = {"guild_id":guild_id, "channel_id": channel_id, "bot_id":bot_id}
        if not await cls.add_guild(q, **q, bili_summary=switch):
            return await Guild.update(q, bili_summary=switch)
        return True

    @classmethod
    async def get_guild(cls, **kwargs):
        """获取频道设置"""
        return await Guild.get(**kwargs).first()

    @classmethod
    async def get_guild_type_id(cls, guild_id, channel_id, bot_id) -> Optional[int]:
        """获取频道订阅 ID"""
        guild = await Guild.get(guild_id=guild_id, channel_id=channel_id, bot_id=bot_id).first()
        return int(guild.guild_id) if guild else None

    @classmethod
    async def get_sub(cls, **kwargs):
        """获取指定位置的订阅信息"""
        return await Sub.get(**kwargs).first()
    
    @classmethod
    async def get_sub_dy(cls, **kwargs):
        """获取指定位置的抖音订阅信息"""
        return await Sub_dy.get(**kwargs).first()

    @classmethod
    async def get_subs(cls, **kwargs):
        return await Sub.get(**kwargs)
    
    @classmethod
    async def get_subs_dy(cls, **kwargs):
        return await Sub_dy.get(**kwargs)

    @classmethod
    async def get_push_list(cls, uid, func) -> List[Sub]:
        """根据类型和 UID 获取需要推送的 QQ 列表"""
        return await cls.get_subs(uid=uid, **{func: True})
    
    @classmethod
    async def get_push_list_dy(cls, sec_uid: str) -> List[Sub_dy]:
        """根据抖音 sec_uid 获取需要推送的 QQ 列表"""
        return await cls.get_subs_dy(sec_uid=sec_uid)

    @classmethod
    async def get_sub_list(cls, type, type_id, bot_id) -> List[Sub]:
        """获取指定位置的推送列表"""
        return await cls.get_subs(type=type, type_id=type_id, bot_id=bot_id)
    
    @classmethod
    async def get_sub_list_dy(cls, group_id, bot_id) -> List[Sub_dy]:
        """获取指定群的抖音推送列表"""
        return await cls.get_subs_dy(group_id=group_id, bot_id=bot_id)

    @classmethod
    async def add_sub(cls, *, name, **kwargs) -> bool:
        """添加订阅"""
        q = {"type":kwargs["type"], "type_id":kwargs["type_id"], "uid":kwargs["uid"], "bot_id":kwargs["bot_id"]}
        if not await Sub.add(q, **kwargs):
            return False
        await cls.add_user(uid=kwargs["uid"], name=name)
        if kwargs["type"] == "group":
            q = {"group_id":kwargs["type_id"], "bot_id": kwargs["bot_id"]}
            await cls.add_group(q, **q, admin=True, decrease_notice=True)
        await cls.update_uid_list()
        return True

    @classmethod
    async def add_sub_dy(cls, **kwargs) -> bool:
        """添加抖音订阅"""
        name = kwargs["name"]
        q = {"group_id":kwargs["group_id"], "bot_id":kwargs["bot_id"], "sec_uid":kwargs["sec_uid"]}
        if not await Sub_dy.add(q, **kwargs):
            return False
        await cls.add_user_dy(sec_uid=kwargs["sec_uid"], name=name, room_id=kwargs["room_id"])
        await cls.update_uid_list_dy()
        return True
    
    @classmethod
    async def update_sub_dy(cls, **kwargs):
        """更新抖音订阅"""
        name = kwargs["name"]
        q = {"group_id":kwargs["group_id"], "bot_id":kwargs["bot_id"], "sec_uid":kwargs["sec_uid"]}
        await Sub_dy.update(q, **q, name = name)

        q = {"sec_uid":kwargs["sec_uid"]}
        await User_dy.update(q, name=name,room_id=kwargs["room_id"])
        await cls.update_uid_list_dy()

    @classmethod
    async def delete_sub(cls, uid, type, type_id, bot_id) -> bool:
        """删除指定订阅"""
        if await Sub.delete(uid=uid, type=type, type_id=type_id, bot_id=bot_id):
            await cls.delete_user(uid=uid)
            await cls.update_uid_list()
            return True
        # 订阅不存在
        return False
    
    @classmethod
    async def delete_sub_dy(cls, sec_uid, group_id, bot_id) -> bool:
        """删除指定抖音订阅"""
        if await Sub_dy.delete(sec_uid=sec_uid, group_id=group_id, bot_id=bot_id):
            await cls.delete_user_dy(sec_uid=sec_uid)
            await cls.update_uid_list_dy()
            return True
        # 抖音订阅不存在
        return False

    @classmethod
    async def delete_sub_list(cls, type, type_id, bot_id):
        """删除指定位置的推送列表"""
        async for sub in Sub.get(type=type, type_id=type_id, bot_id=bot_id):
            await cls.delete_sub(uid=sub.uid, type=sub.type, type_id=sub.type_id, bot_id=bot_id)
        await cls.update_uid_list()

    @classmethod
    async def set_sub(cls, conf, switch, **kwargs):
        """开关订阅设置"""
        return await Sub.update(kwargs, **{conf: switch})

    @classmethod
    async def get_version(cls):
        """获取数据库版本"""
        version = await Version.first()
        return version_parser(version.version) if version else None

    @classmethod
    async def migrate(cls):
        """迁移数据库"""
        DBVERSION = await cls.get_version()
        # 新数据库
        if not DBVERSION:
            # 检查是否有旧的 json 数据库需要迁移
            await cls.migrate_from_json()
            await Version.add(version=str(HBVERSION))
            return
        if DBVERSION != HBVERSION:
            # await cls._migrate()
            await Version.update({}, version=HBVERSION)
            return

    @classmethod
    async def migrate_from_json(cls):
        """从 TinyDB 的 config.json 迁移数据"""
        json_path = Path(get_path("config.json"))
        if not json_path.exists():
            return

        logger.info("正在从 config.json 迁移数据库")
        with json_path.open("r", encoding="utf-8") as f:
            old_db = json.loads(f.read())
        subs: Dict[int, Dict] = old_db["_default"]
        groups: Dict[int, Dict] = old_db["groups"]
        for sub in subs.values():
            await cls.add_sub(
                uid=sub["uid"],
                type=sub["type"],
                type_id=sub["type_id"],
                bot_id=sub["bot_id"],
                name=sub["name"],
                live=sub["live"],
                dynamic=sub["dynamic"],
                at=sub["at"],
            )
        for group in groups.values():
            await cls.set_group_permission(group["group_id"], group["admin"], True)

        json_path.rename(get_path("config.json.bak"))
        logger.info("数据库迁移完成")

    @classmethod
    async def get_uid_list(cls, func) -> List:
        """根据类型获取需要爬取的 UID 列表"""
        return uid_list[func]["list"]
    
    @classmethod
    async def get_uid_list_dy(cls, func) -> List:
        """根据类型获取需要爬取的抖音 sec 列表"""
        return uid_list_dy[func]["list"]

    @classmethod
    async def next_uid(cls, func):
        """获取下一个要爬取的 UID"""
        func = uid_list[func]
        if func["list"] == []:
            return None

        if func["index"] >= len(func["list"]):
            func["index"] = 1
            return func["list"][0]
        else:
            index = func["index"]
            func["index"] += 1
            return func["list"][index]
        
    @classmethod
    async def next_uid_dy(cls, func): # live, dynamic
        """获取下一个要爬取的抖音 sec_id"""
        func = uid_list_dy[func]
        if func["list"] == []:
            return None

        if func["index"] >= len(func["list"]):
            func["index"] = 1
            return func["list"][0]
        else:
            index = func["index"]
            func["index"] += 1
            return func["list"][index]

    @classmethod
    async def update_uid_list(cls):
        """更新需要推送的 UP 主列表"""
        subs = Sub.all()
        uid_list["live"]["list"] = list(
            set([sub.uid async for sub in subs if sub.live])
        )
        uid_list["dynamic"]["list"] = list(
            set([sub.uid async for sub in subs if sub.dynamic])
        )

        # 清除没有订阅的 offset
        dynamic_offset_keys = set(dynamic_offset)
        dynamic_uids = set(uid_list["dynamic"]["list"])
        for uid in dynamic_offset_keys - dynamic_uids:
            del dynamic_offset[uid]
        for uid in dynamic_uids - dynamic_offset_keys:
            dynamic_offset[uid] = -1

    @classmethod
    async def update_uid_list_dy(cls):
        """更新需要推送的抖音 UP 主列表"""
        subs = Sub_dy.all()
        uid_list_dy["live"]["list"] = list(
            set([sub.sec_uid async for sub in subs])
        )
        uid_list_dy["dynamic"]["list"] = uid_list_dy["live"]["list"].copy()

        # 清除没有订阅的 offset
        dynamic_offset_dy_keys = set(dynamic_offset_dy)
        dynamic_uids_dy = set(uid_list_dy["dynamic"]["list"])
        for uid in dynamic_offset_dy_keys - dynamic_uids_dy:
            del dynamic_offset_dy[uid]
        for uid in dynamic_uids_dy - dynamic_offset_dy_keys:
            dynamic_offset_dy[uid] = -1

        # 清除 room_id 为0的直播
        no_live_users = User_dy.get(room_id=0)
        no_live_sets = [u.sec_uid async for u in no_live_users]

        live_list = uid_list_dy["live"]["list"]
        for i in range(len(live_list)-1, -1, -1):
            if live_list[i] in no_live_sets:
                del live_list[i]

    async def backup(self):
        """备份数据库"""
        pass

    @classmethod
    async def get_login(cls):
        """获取登录信息"""
        pass

    @classmethod
    async def update_login(cls, tokens):
        """更新登录信息"""
        pass


get_driver().on_startup(DB.init)
get_driver().on_shutdown(connections.close_all)
