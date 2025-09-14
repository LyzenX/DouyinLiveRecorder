# coding=utf-8
"""
:author: Lyzen
:date: 2023.04.03
:brief: app主文件
"""

import os
import signal
import sys
import logging
import platform
import threading

from dylr.core import version, config, record_manager, monitor, cli_state_manager
from dylr.util import logger
from dylr.plugin import plugin

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
        print(f'软件仅供科研数据挖掘与学习交流，因错误使用而造成的危害由使用者负责。')
        print('=' * 80)

    config.read_configs()
    if config.debug():
        logger.instance.setLevel(logging.DEBUG)
    record_manager.rooms = config.read_rooms()

    if config.is_cli_key_l_enable():
        t = threading.Thread(target=cli_state_manager.run)
        # t.setDaemon(True)
        t.start()

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
    lack_dependencies = []
    try:
        import requests
    except:
        lack_dependencies.append('requests')
    try:
        import websocket
    except:
        lack_dependencies.append('websocket-client')
    try:
        import google.protobuf
    except:
        lack_dependencies.append('protobuf')
    try:
        import gmssl
    except:
        lack_dependencies.append('gmssl')

    if win_mode:
        if sys.platform == 'win32':
            os.system(f'start cmd /C "chcp 65001 & '
                      f'echo 缺少依赖{lack_dependencies}，请运行(安装依赖.bat)或运行命令(python -m pip install -r requirements.txt) & '
                      f'pause"')
        else:
            print(f'echo 缺少依赖{lack_dependencies}，请运行(安装依赖.bat)或运行命令(python -m pip install -r requirements.txt)')
    return False
