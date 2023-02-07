# coding=utf-8
"""
用来提供自定义扩展
你可以在 plugin 目录下创建自己的自定义 python 脚本
然后将运行方式放在下面的方法中
比如当直播开始录制时，进行推送
"""
from dylr.util import logger
import dylr.core.record_manager


def on_open(gui: bool):
    """
     软件刚启动时
     :param gui: 是否以GUI形式启动
    """
    ...


def on_loaded(gui: bool):
    """
     软件加载完成时，此时配置、房间等已加载完成
     :param gui: 是否以GUI形式启动
    """
    ...


def on_close():
    """
    软件关闭时
    若强制关闭可能不会触发
    """
    ...


def on_live_start(room, filename):
    """
    直播开始时
    :param room: 直播间
    :param filename: 录制的文件名(包含相对路径)
    """
    ...


def on_live_end(room, file):
    """
    直播结束时
    :param room: 直播间
    :param file: 录制的文件名，可以通过 room.record_danmu 来获取是否录制弹幕，弹幕文件名与视频名一致，但后缀名为 xml
    """
    ...


def on_cookie_invalid():
    """
    当cookie失效时
    也可能是抖抖接口失效
    """
    ...


def get_recordings() -> list:
    """
    获取正在录制的直播列表
    :return: list: core.recording.Recording
    """
    return dylr.core.record_manager.get_recordings()


def get_rooms() -> list:
    """
    获取所有已添加的房间，包括添加但不自动录制的
    :return: list: core.room.Room
    """
    return dylr.core.record_manager.get_rooms()


def get_logger():
    """
    获取 logger 以便在同一个 log 文件记录日志
    """
    return logger
