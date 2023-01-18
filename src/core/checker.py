# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 直播开播检测
"""

import time
import threading
from threading import Thread

import requests
from selenium.webdriver.common.by import By

from src.util import logger, cookie_utils
from src.core.browser import Browser
from src.core import config, record_manager, recorder, app


def init():
    if not config.is_using_custom_cookie():
        cookie_utils.auto_get_cookie()

    start_thread()

    while True:
        time.sleep(0.1)
        if app.stop_all_threads:
            time.sleep(1)  # 给时间让其他线程结束
            break


def start_thread():
    t = Thread(target=check_thread_main)
    t.setDaemon(True)
    t.start()


check_rooms = []
lock = threading.Lock()


def check_thread_main():
    if not record_manager.get_auto_record_rooms():
        logger.info_and_print('检测房间列表为空')
    global check_rooms
    while True:
        # logger.debug_and_print('new task for checking')
        check_rooms = record_manager.get_rooms_needed_to_record()
        for i in range(config.get_check_threads()):
            t = Thread(target=check_thread_task)
            t.start()
        while check_rooms:
            time.sleep(0.1)
        time.sleep(config.get_check_period())


def check_thread_task():
    global check_rooms
    while check_rooms:
        lock.acquire()
        room = check_rooms.pop()
        lock.release()

        if app.stop_all_threads:
            break

        # 如果房间被移除，但本次检测已经包含了该房间，则不检测该房间
        if room not in record_manager.rooms:
            continue

        check_room(room)
        time.sleep(0.2)  # 防止极短时间内过多请求造成的请求过于频繁


def check_room(room):
    if config.is_monitor_using_api():
        check_room_using_api(room)
    else:
        check_room_using_browser(room)


def check_room_using_api(room):
    # logger.debug_and_print(f'checking {room.room_name}({room.room_id})')
    api_url = recorder.get_api_url(room.room_id)
    req = requests.get(api_url, headers=recorder.get_request_headers())
    res = req.text
    if '"status":2' in res and 'stream_url' in res:
        logger.info_and_print(f'检测到 {room.room_name}({room.room_id}) 开始直播，启动录制。')
        recorder.start_recording(room)
    if '系统繁忙，请稍后再试' in res:
        cookie_utils.record_cookie_failed()


def check_room_using_browser(room):
    # logger.debug_and_print(f'checking {room.room_name}({room.room_id})')

    browser = Browser()

    browser.open(f'https://live.douyin.com/{room.room_id}')
    browser.driver.implicitly_wait(10)
    time.sleep(1)
    browser.driver.execute_cdp_cmd(
        'Page.addScriptToEvaluateOnNewDocument',
        {'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'}
    )
    video_tags = browser.driver.find_elements(By.TAG_NAME, "video")
    if video_tags:
        logger.info_and_print(f'检测到 {room.room_name}({room.room_id}) 开始直播，启动录制。')
        recorder.start_recording(room, browser)
    else:
        browser.quit()
        # logger.debug_and_print(f'{room.room_name}({room.room_id}) has not live')
