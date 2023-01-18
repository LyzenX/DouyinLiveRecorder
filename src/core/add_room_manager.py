# coding=utf-8

import json
import re
import threading
import time
from functools import partial
from tkinter import messagebox

import requests

from src.core import app, recorder, record_manager, config, checker
from src.core.browser import Browser
from src.core.room import Room
from src.util import logger, cookie_utils

re_num = re.compile(r'^\d*$')
re_live = re.compile(r'^(http:|https:)?(//)?live.douyin.com/\d*')
re_short = re.compile(r'^(http:|https:)?(//)?v.douyin.com/')
re_user = re.compile(r'^(http:|https:)?(//)?(www.)?douyin.com/user/')


def try_add_room(info):
    try:
        if re_num.match(info):
            find_web_rid(info)
            return
        elif re_live.match(info):
            find_live(info)
            return
        elif re_short.match(info):
            find_short(info)
            return
        elif re_user.match(info):
            find_user(info)
            return
    except Exception:
        pass
    logger.error_and_print("添加主播失败，请确认输入的内容是否符合要求\n如果符合要求，可能是抖音作了修改导致失效，请换种方式。")
    if app.win_mode:
        messagebox.askokcancel("添加主播失败", "请确认输入的内容是否符合要求\n如果符合要求，可能是抖音作了修改导致失效，请换种方式。")


def find_live(info):
    info = info[info.index('.com/') + 5:]
    if '?' in info:
        info = info[:info.index('?')]
    find_web_rid(info)


def find_web_rid(info):
    room = record_manager.get_room(info)
    if room is not None:
        logger.error_and_print(f'重复获取主播房间: {room.room_name}({info})')
        if app.win_mode:
            messagebox.askokcancel("房间已存在", f"重复获取主播房间: {room.room_name}({info})")
        return

    resp = requests.get(recorder.get_api_url(info), headers=recorder.get_request_headers())
    json_info = json.loads(resp.text)
    name = json_info['data']['user']['nickname']
    if name is None or len(name) == 0:
        raise Exception()
    room = Room(info, name, True, True)
    record_manager.rooms.append(room)
    config.save_rooms()

    # 添加完房间立刻检查是否开播
    def check(room):
        checker.check_room(room)
    threading.Thread(target=partial(check, room)).start()

    logger.info_and_print(f'成功获取到房间{name}({info})')
    if app.win_mode:
        app.win.add_room(room)
        messagebox.askokcancel("添加主播成功", f"房间Web_Sid: {info} \n"
                                         f"主播名: {name}")


def find_short(info):
    browser = Browser()
    browser.open('https://www.douyin.com')
    cookies = cookie_utils.str2cookies(cookie_utils.cookie_cache)
    for cookie in cookies:
        browser.driver.add_cookie(cookie)
    browser.driver.refresh()
    browser.open(info)
    for i in range(10):
        if app.stop_all_threads:
            browser.quit()
            return
        time.sleep(1)
        url = browser.driver.current_url
        if re_live.match(url):
            browser.quit()
            find_live(url)
            return
    browser.quit()
    raise Exception()


def find_user(info):
    resp = requests.get(info, headers=recorder.get_request_headers())
    index = resp.text.index('https://live.douyin.com/')
    res = resp.text[index:]
    res = res[:res.index('?')]
    find_live(res)
