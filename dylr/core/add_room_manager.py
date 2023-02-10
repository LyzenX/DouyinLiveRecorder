# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.17
:brief: 通过 Web_Rid、直播间地址、直播间短链、(正在直播的)主播主页 获取主播房间信息
"""

import re
import time
import threading
from functools import partial
from tkinter import messagebox

import requests

from dylr.core.room import Room
from dylr.core.browser import Browser
from dylr.util import logger, cookie_utils
from dylr.core import app, record_manager, config, monitor, dy_api

# Web_Rid 纯数字
re_num = re.compile(r'^\d*$')
# 使用 Web_Rid 的网址
re_live = re.compile(r'^(http:|https:)?(//)?live.douyin.com/\d*')
# 短链
re_short = re.compile(r'^(http:|https:)?(//)?v.douyin.com/')
# 用户主页
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
    """ live.douyin.com/xxx """
    info = info[info.index('.com/') + 5:]
    if '?' in info:
        info = info[:info.index('?')]
    find_web_rid(info)


def find_web_rid(web_rid):
    """ web_rid number """
    room = record_manager.get_room(web_rid)
    if room is not None:
        logger.error_and_print(f'重复获取主播房间: {room.room_name}({web_rid})')
        if app.win_mode:
            messagebox.askokcancel("房间已存在", f"重复获取主播房间: {room.room_name}({web_rid})")
        return

    # api 1 暂时失效
    # resp = requests.get(recorder.get_api_url1(info), headers=recorder.get_request_headers())
    # json_info = json.loads(resp.text)

    # api 2
    json_info = dy_api.get_live_state_json(web_rid)
    name = json_info['owner']['nickname']

    if name is None or len(name) == 0:
        raise Exception()
    room = Room(web_rid, name, True, True, False)
    record_manager.rooms.append(room)
    config.save_rooms()

    # 添加完房间立刻检查是否开播
    threading.Thread(target=partial(monitor.check_room, room)).start()

    logger.info_and_print(f'成功获取到房间{name}({web_rid})')
    if app.win_mode:
        app.win.add_room(room)
        messagebox.askokcancel("添加主播成功", f"房间Web_Sid: {web_rid} \n 主播名: {name}")


def find_short(info):
    """ v.douyin.com/xxx """
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
    """ www.douyin.com/user/xxx """
    resp = requests.get(info, headers=dy_api.get_request_headers())
    index = resp.text.index('https://live.douyin.com/')
    res = resp.text[index:]
    res = res[:res.index('?')]
    find_live(res)
