# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 直播开播检测
"""
import random
import time
import threading
import traceback
from functools import partial
from threading import Thread

import requests
from selenium.webdriver.common.by import By

from dylr.util import logger, cookie_utils
from dylr.core.browser import Browser
from dylr.core import config, record_manager, recorder, app, danmu_recorder, monitor_thread_manager


def init():
    if not config.is_using_custom_cookie():
        cookie_utils.auto_get_cookie()

    start_thread()

    while True:
        time.sleep(0.1)
        if app.stop_all_threads:
            time.sleep(1)  # 给时间让其他线程结束
            break


important_threads = []


def start_thread():
    t = Thread(target=check_thread_main)
    t.setDaemon(True)
    t.start()

    # 重要主播，每个都开一个独立线程
    for room in record_manager.get_important_rooms():
        start_important_monitor_thread(room)


def start_important_monitor_thread(room):
    t = Thread(target=partial(important_monitor, room))
    t.setDaemon(True)
    t.start()


def important_monitor(room):
    important_threads.append(str(room.room_id))
    while True:
        # 房间被移除
        if room not in record_manager.rooms:
            important_threads.remove(str(room.room_id))
            break

        # 房间被设置为不重要
        if not room.important:
            important_threads.remove(str(room.room_id))
            break

        if not record_manager.is_recording(room):
            try:
                check_room(room)
            except Exception as err:
                logger.fatal_and_print(traceback.format_exc())
                pass  # 防止报错停止检测线程
        time.sleep(config.get_important_check_period() +
                   random.uniform(0, config.get_important_check_period_random_offset()))


check_rooms = []
lock = threading.Lock()


def check_thread_main():
    if not record_manager.get_monitor_rooms():
        logger.info_and_print('检测房间列表为空')
    global check_rooms
    while True:
        # logger.debug_and_print('new task for checking')
        check_rooms = record_manager.get_monitor_rooms()
        check_rooms.reverse()
        futures = []
        for i in range(config.get_check_threads()):
            futures.append(monitor_thread_manager.new_check_task(check_thread_task))
        # 等待所有检测线程完成本轮检测
        for future in futures:
            future.result()
        # 等待一定时间后再进行下一轮检测
        time.sleep(config.get_check_period()+random.uniform(0, config.get_check_period_random_offset()))


def check_thread_task():
    global check_rooms
    while True:
        lock.acquire()
        if check_rooms:
            room = check_rooms.pop()
            lock.release()
        else:
            lock.release()
            break

        if app.stop_all_threads:
            break

        # 如果房间被移除，但本次检测已经包含了该房间，则不检测该房间
        if room not in record_manager.rooms:
            continue

        start_time = time.time()
        try:
            check_room(room)
        except Exception as err:
            logger.fatal_and_print(traceback.format_exc())
            pass  # 防止报错停止检测线程

        end_time = time.time()
        cost_time = end_time - start_time
        if cost_time <= config.get_check_wait_time():
            # 房间间等待间隔，防止极短时间内检测过多而被屏蔽
            time.sleep(config.get_check_wait_time() - cost_time)


def check_room(room):
    if config.is_monitor_using_api():
        try:
            check_room_using_api(room)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ReadTimeout):
            logger.debug(traceback.format_exc())
    else:
        check_room_using_browser(room)


def check_room_using_api(room):
    # logger.debug_and_print(f'checking {room.room_name}({room.room_id})')

    # api1
    # api_url = recorder.get_api_url1(room.room_id)
    # proxies = {"http": None, "https": None}
    # req = requests.get(api_url, headers=recorder.get_request_headers(), proxies=proxies)
    # res = req.text
    # print(res)
    # if ('"status":2' in res or "'status':2" in res) and 'stream_url' in res:

    # api2
    room_json = recorder.get_live_state_json(room.room_id)
    if room_json['status'] == 2:
        logger.info_and_print(f'检测到 {room.room_name}({room.room_id}) 开始直播，启动录制。')

        now = time.localtime()
        now_str = time.strftime('%Y%m%d_%H%M%S', now)
        filename = f"download/{room.room_name}/{now_str}.flv"

        def rec_thread():
            stream_url = room_json['stream_url']['flv_pull_url']['FULL_HD1']
            recorder.start_recording(room, filename=filename, stream_url=stream_url)

        def danmu_thread():
            danmu_recorder.start_recording(room, browser=None, start_time=now)

        threading.Thread(target=rec_thread).start()
        if room.record_danmu:
            threading.Thread(target=danmu_thread).start()
    # if '系统繁忙，请稍后再试' in res or '当前服务繁忙，请稍后重试' in res:
    #     cookie_utils.record_cookie_failed()


def check_room_using_browser(room):
    # logger.debug_and_print(f'checking {room.room_name}({room.room_id})')

    browser = Browser()

    browser.open(f'https://live.douyin.com/{room.room_id}')
    browser.driver.implicitly_wait(10)
    time.sleep(1)
    browser.send_cdp_cmd()
    video_tags = browser.driver.find_elements(By.TAG_NAME, "video")
    if video_tags:
        logger.info_and_print(f'检测到 {room.room_name}({room.room_id}) 开始直播，启动录制。')

        now = time.localtime()
        now_str = time.strftime('%Y%m%d_%H%M%S', now)
        filename = f"download/{room.room_name}/{now_str}.flv"

        def rec_thread():
            recorder.start_recording(room, browser, filename)

        def danmu_thread():
            danmu_recorder.start_recording(room, browser=browser, start_time=now)

        threading.Thread(target=rec_thread).start()
        if room.record_danmu:
            threading.Thread(target=danmu_thread).start()
    else:
        browser.quit()
        # logger.debug_and_print(f'{room.room_name}({room.room_id}) has not live')
