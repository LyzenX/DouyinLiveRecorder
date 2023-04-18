# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 直播开播检测
"""
import time
import random
import threading
import traceback
from threading import Thread

import requests

from dylr.core.room_info import RoomInfo
from dylr.util import logger, cookie_utils
from dylr.core import config, record_manager, app, dy_api, monitor_thread_manager

# 重要房间检测线程
important_room_threads = []
# 本轮检测中需要检测房间的队列
check_rooms_queue = []


def init():
    cookie_utils.auto_get_cookie()

    start_thread()

    while True:
        time.sleep(0.1)
        if app.stop_all_threads:
            time.sleep(1)  # 给时间让其他线程结束
            break


def start_thread():
    # 启动主检测线程
    t = Thread(target=check_thread_main)
    t.setDaemon(True)
    t.start()

    # 重要主播，每个都开一个独立线程
    for room in record_manager.get_important_rooms():
        start_important_monitor_thread(room)
        # 将几个重要主播的检测时间错开，避免重要主播过多时，一秒内同时检测太多
        time.sleep(0.97)


def start_important_monitor_thread(room):
    t = Thread(target=important_monitor, args=(room,))
    t.setDaemon(True)
    t.start()


def important_monitor(room):
    important_room_threads.append(str(room.room_id))
    while True:
        # 房间被移除
        if room not in record_manager.rooms:
            important_room_threads.remove(str(room.room_id))
            break

        # 房间被设置为不重要
        if not room.important:
            important_room_threads.remove(str(room.room_id))
            break

        if not record_manager.is_recording(room):
            try:
                check_room(room)
            except Exception as err:
                logger.fatal_and_print(traceback.format_exc())
                pass  # 防止报错停止检测线程
        time.sleep(config.get_important_check_period() +
                   random.uniform(0, config.get_important_check_period_random_offset()))


def check_thread_main():
    if not record_manager.get_monitor_rooms():
        logger.info_and_print('检测房间列表为空')
    global check_rooms_queue
    while True:
        # logger.debug_and_print('new task for checking')
        check_rooms_queue = record_manager.get_monitor_rooms()
        check_rooms_queue.reverse()
        futures = []
        for i in range(config.get_check_threads()):
            futures.append(monitor_thread_manager.new_check_task(check_thread_task))
        # 等待所有检测线程完成本轮检测
        for future in futures:
            future.result()
        # 等待一定时间后再进行下一轮检测
        time.sleep(config.get_check_period()+random.uniform(0, config.get_check_period_random_offset()))


def check_thread_task():
    global check_rooms_queue
    while True:
        if check_rooms_queue:
            room = check_rooms_queue.pop()
        else:
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
    try:
        check_room_using_api(room)
    except (requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ProxyError):
        logger.debug(traceback.format_exc())


def check_room_using_api(room):
    # logger.debug_and_print(f'checking {room.room_name}({room.room_id})')

    room_json = dy_api.get_live_state_json(room.room_id)
    if room_json is None:
        cookie_utils.record_cookie_failed()
        return
    room_info = RoomInfo(room, room_json)
    if room_info.is_going_on_live():
        logger.info_and_print(f'检测到 {room.room_name}({room.room_id}) 开始直播，启动录制。')

        record_manager.start_recording(room, room_info)
