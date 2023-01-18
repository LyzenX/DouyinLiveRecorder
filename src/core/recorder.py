# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 录制器核心
"""

import json
import time
import os.path
from threading import Thread

import requests
from requests.adapters import HTTPAdapter
from selenium.webdriver.common.by import By

from src.plugin import plugin
from src.core.browser import Browser
from src.util import logger, cookie_utils
from src.core.recording import Recording
from src.core import config, record_manager, checker, transcode_manager, app


def start_recording(room, browser=None):
    # 获取直播视频流链接
    stream_url = find_stream_url(room)
    if stream_url is not None:
        logger.debug(f'find stream url of {room.room_name}({room.room_id}): {stream_url}. Starting downloading...')
    else:
        logger.error(f'{room.room_name}({room.room_id} 获取直播资源链接失败')
        logger.debug(f'filed to find stream url of {room.room_name}({room.room_id}).')
        if browser is not None:
            browser.quit()
        return

    # 视频名
    now = time.localtime()
    now_str = time.strftime('%Y%m%d_%H%M%S', now)
    filename = f"download/{room.room_name}/{now_str}.flv"

    # 开始录制，但房间被移除，不录制了
    if room not in record_manager.rooms:
        if browser is not None:
            browser.quit()
        return

    # 防止重复录制
    if record_manager.is_recording(room):
        logger.warning_and_print(f'{room.room_name}({room.room_id} 已经在录制了')
        if browser is not None:
            browser.quit()
        return

    # 获取成功，清除 cookie failed 记录
    cookie_utils.cookie_failed = 0

    rec = Recording(room, filename)
    record_manager.recordings.append(rec)
    plugin.on_live_start(room)

    # GUI
    if app.win_mode:
        app.win.set_state(room, '正在录制', color='#0000bb')

    def download():
        s = requests.Session()
        s.mount(stream_url, HTTPAdapter(max_retries=3))
        downloading = s.get(
            stream_url, timeout=(5, 10), verify=False, stream=True
        )
        if not os.path.exists('download'):
            os.mkdir('download')
        if not os.path.exists(f'download/{room.room_name}'):
            os.mkdir(f'download/{room.room_name}')

        with open(filename, 'wb') as file:
            try:
                for data in downloading.iter_content(chunk_size=1024):
                    if data:
                        file.write(data)
                        if rec.stop_signal:  # 主动停止录制
                            logger.info_and_print(f'主动停止{room.room_name}({room.room_id}的录制')
                            break
            except requests.exceptions.ConnectionError as err:
                # 下载失败(一般是下载超时)，可能是直播已结束，或主播长时间卡顿，先结束录制，然后再检测是否在直播
                pass
        # 结束录制
        record_manager.recordings.remove(rec)
        logger.info_and_print(f'{room.room_name}({room.room_id}) 录制结束')
        plugin.on_live_end(room, filename)

        # GUI
        if app.win_mode:
            app.win.set_state(room, '未开播', color='#000000')

        # 自动转码
        if config.is_auto_transcode():
            transcode_manager.start_transcode(filename)

        # 再次检测是否在直播，防止因网络问题造成的提前停止录制
        # 如果是主动停止录制，则不立刻再次检查
        if rec.stop_signal:
            checker.check_room(room)

    t = Thread(target=download)
    t.setDaemon(True)
    t.start()

    # 弹幕录制
    if room.record_danmu:
        record_danmu(room, now_str, browser)
    elif browser is not None:
        browser.quit()  # 关闭浏览器，清除缓存，以修复缓存爆炸的bug


def find_stream_url(room):
    room_id = room.room_id

    url = get_api_url(room_id)
    resp = requests.get(url, headers=get_request_headers())

    if '系统繁忙，请稍后再试' in resp:
        cookie_utils.record_cookie_failed()

    try:
        json_info = json.loads(resp.text)
    except:
        logger.debug(f'failed to load response of GET to json when finding stream url of {room.room_name}({room_id}).'
                     f' response: ' + resp.text)
        return None

    try:
        if 'data' in json_info and 'data' in json_info['data']:
            data = json_info['data']['data']
            stream_url = data[0]['stream_url']
            flv_pull_url = stream_url['flv_pull_url']
            flv_url = flv_pull_url['FULL_HD1']

            return flv_url
        else:
            logger.debug(f'failed to read json when finding stream url of {room.room_name}({room_id}).'
                         f' json: ' + str(json_info))
    except:
        logger.debug(f'failed to read json when finding stream url of {room.room_name}({room_id}).'
                     f' json: ' + str(json_info))
    return None


def get_api_url(room_id):
    return "https://live.douyin.com/webcast/web/enter/?aid=6383&live_id=1&device_platform=web" \
          "&language=zh-CN&enter_from=web_live&cookie_enabled=true&screen_width=1536&screen_height=864" \
          "&browser_language=zh-CN&browser_platform=Win32&browser_name=Chrome&browser_version=94.0.4606.81" \
          f"&room_id_str=&enter_source=&web_rid={room_id}"


def get_request_headers():
    return {
        'user-agent': '"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                      ' (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"',
        'cookie': cookie_utils.cookie_cache
    }


def record_danmu(room, filename, browser=None):
    if browser is None:
        # 新开浏览器，需要填入 cookie 并刷新
        logger.debug(f'start recording danmu for {room.room_name}({room.room_id}). browser not passed.')
        browser = Browser()
        browser.open(f'https://live.douyin.com/{room.room_id}')
        cookies = cookie_utils.str2cookies(cookie_utils.cookie_cache)
        for cookie in cookies:
            browser.driver.add_cookie(cookie)
        browser.driver.refresh()
        browser.driver.implicitly_wait(10)
        time.sleep(1)
        browser.driver.execute_cdp_cmd(
            'Page.addScriptToEvaluateOnNewDocument',
            {'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'}
        )
        video_tags = browser.driver.find_elements(By.TAG_NAME, "video")
        if not video_tags:
            logger.error(f'{room.room_name}({room.room_id})录制弹幕失败：无法加载直播')
            return
    else:
        # 开播检测传来了浏览器，不必刷新网页
        cookies = cookie_utils.str2cookies(cookie_utils.cookie_cache)
        for cookie in cookies:
            browser.driver.add_cookie(cookie)
        logger.debug(f'start recording danmu for {room.room_name}({room.room_id}). browser passed.')

    logger.info_and_print(f'开始录制 {room.room_name}({room.room_id}) 的弹幕')

    # 判断是否能加载弹幕
    # 可能的bug：如果长时间没人进入直播间，则可能会认为无法加载弹幕
    retry = 0
    while retry < 3:
        # 判断弹幕是否可以加载出来
        tag = browser.driver.find_elements(By.CLASS_NAME, "webcast-chatroom___item")
        if len(tag) > 0:
            break
        # 弹幕加载不出来
        retry += 1
        browser.driver.refresh()
        browser.driver.implicitly_wait(10)
        cookie_utils.record_cookie_failed()
    if retry == 3:
        logger.error_and_print(f'{room.room_name}({room.room_id}) 弹幕录制失败：无法加载弹幕，可能是cookie失效了？')
        browser.quit()
        return

    # 写入文件头部数据
    with open(f'download/{room.room_name}/{filename}.xml', 'a', encoding='UTF-8') as file:
        file.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
                   "<?xml-stylesheet type=\"text/xsl\" href=\"#s\"?>\n"
                   "<i>\n")

    start_time = time.time()
    danmu = {}
    while True:
        if not record_manager.is_recording(room):
            # 直播结束，弹幕录制也结束
            break

        # 分析并从 html 中获取弹幕
        elements = browser.driver.find_elements(By.CLASS_NAME, 'webcast-chatroom___item')
        for element in elements:
            if app.stop_all_threads:
                # 软件被强制停止，写入文件尾，以免弹幕文件不完整而无法使用
                if len(danmu) > 0:
                    with open(f'download/{room.room_name}/{filename}.xml', 'a', encoding='UTF-8') as file:
                        file.write('</i>')
                browser.quit()
                return
            try:
                data_id = str(element.get_attribute('data-id'))
                if data_id in danmu:
                    continue

                inner_div = element.find_elements(By.TAG_NAME, 'div')[0]

                # 忽略欢迎来到直播间的提示
                if inner_div.get_attribute('class') == 'webcast-chatroom__room-message':
                    continue

                text = inner_div.text
                # 忽略用户来了的提示
                if '：' not in text and '来了' in text:
                    continue
                # 忽略送礼
                if '送出了 × ' in text:
                    continue
                # 去除用户名前面的各种花里胡哨的前缀
                if '\n' in text:
                    text = text[text.index('\n')+1:].strip()

                # print(text)  # 在控制台中输出弹幕

                user = text[:text.index('：')]
                mes = text[text.index('：')+1:]

                now = time.time()
                danmu[data_id] = {
                    'user': user,
                    'message': mes,
                    'time': now
                }

                second = now - start_time
                # 写入单条数据
                with open(f'download/{room.room_name}/{filename}.xml', 'a', encoding='UTF-8') as file:
                    file.write(f"  <d p=\"{round(second, 2)},1,25,16777215,"
                               f"{int(now*1000)},0,1602022773,0\" user=\"{user}\">{mes}</d>\n")

            except Exception:
                pass
        time.sleep(0.2)
    # 写入文件尾
    with open(f'download/{room.room_name}/{filename}.xml', 'a', encoding='UTF-8') as file:
        file.write('</i>')
    logger.info_and_print(f'{room.room_name}({room.room_id}) 弹幕录制结束')
    browser.quit()  # 关闭浏览器，清除缓存，以修复缓存爆炸的bug
