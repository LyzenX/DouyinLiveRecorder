# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 房间记录类
"""


class Room:
    def __init__(self, room_id: str, room_name: str, auto_record: bool, record_danmu: bool, important: bool,
                 user_sec_id: str = None):
        self.room_id = room_id
        self.room_name = room_name
        self.auto_record = auto_record
        self.record_danmu = record_danmu
        self.important = important
        self.user_sec_id = user_sec_id

    def set_auto_record(self, b: bool):
        self.auto_record = b
