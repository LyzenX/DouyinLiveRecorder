# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 正在录制的直播类
"""


class Recording:
    def __init__(self, room, filename):
        self.room = room
        self.filename = filename
        self.stop_signal = False

    def stop(self):
        self.stop_signal = True
