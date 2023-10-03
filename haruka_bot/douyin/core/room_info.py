# coding=utf-8
"""
:author: Lyzen
:date: 2023.02.10
:brief: 检测的房间信息，包含是否开播、流地址等
"""
from ..utils_dy import cookie_utils


class RoomInfo:
    def __init__(self, room_json):
        self.room_json = room_json

    def get_real_room_id(self):
        """ 获取 id_str , 不是 web_rid """
        return self.room_json['id_str']

    async def is_going_on_live(self) -> bool:
        """ 是否在直播 """
        if not self.room_json or 'status' not in self.room_json:
            await cookie_utils.record_cookie_failed()
            return False
        return self.room_json['status'] == 2

    def get_stream_url(self):
        """ 直播流地址 """
        if not self.room_json or 'stream_url' not in self.room_json:
            return None
        return self.room_json['stream_url']['flv_pull_url']['FULL_HD1']

    def get_nick_name(self):
        """ 主播名 """
        if not self.room_json or 'owner' not in self.room_json:
            return None
        return self.room_json['owner']['nickname']
    
    def get_title(self):
        """获取直播标题"""
        return self.room_json['title']
    
    def get_cover_url(self):
        """获取直播封面"""
        return self.room_json['cover']['url_list'][0]