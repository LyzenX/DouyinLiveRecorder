# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.16
:brief: app主文件
"""

import os
import signal
import sys
import logging
import platform
import threading

from dylr.util import logger
from dylr.plugin import plugin
from dylr.core import version, config, record_manager, monitor

win_mode = False
win = None
# 处理 ctrl+c
stop_all_threads = False


def init(gui_mode: bool):
    global win_mode
    win_mode = gui_mode
    # 处理 ctrl+c
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)

    if not check_dependencies():
        return

    plugin.on_open(gui_mode)

    logger.info(f'software started. version: {version}. gui: {gui_mode}.')
    logger.info(f'platform: {platform.platform()}')
    logger.info(f'python version: {platform.python_version()}')
    if not gui_mode:
        if sys.platform == 'win32':
            os.system('chcp 65001')
        print('=' * 80)
        print(f'Douyin Live Recorder v.{version} by Lyzen')
        print(f'吾爱破解论坛')
        print(f'软件仅供学习交流使用，禁止商业使用，禁止用来做危害网络安全的事情，因错误使用造成的危害由使用者负责。')
        print('=' * 80)

    config.read_configs()
    if config.debug():
        logger.instance.setLevel(logging.DEBUG)
    record_manager.rooms = config.read_rooms()

    plugin.on_loaded(gui_mode)

    if gui_mode:
        t = threading.Thread(target=monitor.init)
        t.start()
        start_gui()
    else:
        monitor.init()


def start_gui():
    global stop_all_threads
    from dylr.gui import app_win
    app_win.ApplicationWin()
    # GUI被关闭时，继续往下运行
    stop_all_threads = True
    logger.info_and_print('GUI closed')
    plugin.on_close()


def sigint_handler(signum, frame):
    global stop_all_threads
    stop_all_threads = True
    logger.fatal_and_print('catched SIGINT(Ctrl+C) signal')
    plugin.on_close()


def check_dependencies():
    has_requests = True
    has_selenium = True
    has_webdriver_manager = True
    try:
        import requests
    except:
        has_requests = False
    try:
        import selenium
    except:
        has_selenium = False
    try:
        import webdriver_manager
    except:
        has_webdriver_manager = False

    if has_requests and has_selenium and has_webdriver_manager:
        return True
    res = []
    if not has_requests:
        res.append('requests')
    if not has_selenium:
        res.append('selenium')
    if not has_webdriver_manager:
        res.append('webdriver_manager')

    if win_mode:
        if sys.platform == 'win32':
            os.system(f'start cmd /C "chcp 65001 & '
                      f'echo 缺少依赖{res}，请运行(安装依赖.bat)或运行命令(python -m pip install -r requirements.txt) & '
                      f'pause"')
        else:
            print(f'echo 缺少依赖{res}，请运行(安装依赖.bat)或运行命令(python -m pip install -r requirements.txt)')
    return False
