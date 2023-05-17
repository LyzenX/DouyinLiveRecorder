# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 录制器核心
"""

import time
import os.path

from threading import Thread

import requests
from requests.adapters import HTTPAdapter

from dylr.plugin import plugin
from dylr.core import app, config, monitor, record_manager, transcode_manager, dy_api
from dylr.core.recording import Recording
from dylr.util import logger, cookie_utils


def start_recording(room, browser=None, filename=None, stream_url=None):
    """ 启动录制 """
    if filename is None:
        now = time.localtime()
        now_str = time.strftime('%Y%m%d_%H%M%S', now)
        download_path = config.get_download_path()
        filename = f"{download_path}/{room.room_name}/{now_str}.flv"

    # 获取直播视频流链接
    if stream_url is None:
        stream_url = dy_api.find_stream_url(room)
        if stream_url is not None:
            logger.debug(f'find stream url of {room.room_name}({room.room_id}): {stream_url}. Starting downloading...')
        else:
            logger.error_and_print(f'{room.room_name}({room.room_id}) 获取直播资源链接失败')
            cookie_utils.record_cookie_failed()
            if browser is not None:
                browser.quit()
            return

    # 开始录制，但房间被移除，不录制了
    if room not in record_manager.rooms:
        if browser is not None:
            browser.quit()
        return

    # 防止重复录制
    if record_manager.is_recording(room):
        logger.warning_and_print(f'{room.room_name}({room.room_id}) 已经在录制了')
        if browser is not None:
            browser.quit()
        return

    # 获取成功，清除 cookie failed 记录
    cookie_utils.cookie_failed = 0

    rec = Recording(room, filename)
    record_manager.recordings.append(rec)
    plugin.on_live_start(room, filename)

    # GUI
    if app.win_mode:
        app.win.set_state(room, '正在录制', color='#0000bb')

    def download():
        s = requests.Session()
        s.mount(stream_url, HTTPAdapter(max_retries=3))
        for retry in range(1, 5):
            if retry == 4:
                logger.error_and_print(f'{room.room_name}({room.room_id})直播获取超时。')
                rec.stop()
                record_manager.recordings.remove(rec)
                return
            try:
                downloading = s.get(
                    stream_url, timeout=(5, 10), verify=False, stream=True
                )
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                logger.error_and_print(f'{room.room_name}({room.room_id})直播获取超时，正在重试({retry})')
        download_path = config.get_download_path()
        if not os.path.exists(download_path):
            os.mkdir(download_path)
        if not os.path.exists(f'{download_path}/{room.room_name}'):
            os.mkdir(f'{download_path}/{room.room_name}')

        with open(filename, 'wb') as file:
            try:
                for data in downloading.iter_content(chunk_size=1024):
                    if data:
                        file.write(data)
                        if rec.stop_signal:  # 主动停止录制
                            logger.info_and_print(f'主动停止{room.room_name}({room.room_id})的录制')
                            break
            except requests.exceptions.ConnectionError:
                # 下载出错(一般是下载超时)，可能是直播已结束，或主播长时间卡顿，先结束录制，然后再检测是否在直播
                pass
        # 结束录制
        record_manager.recordings.remove(rec)
        logger.info_and_print(f'{room.room_name}({room.room_id}) 录制结束')
        plugin.on_live_end(room, filename)

        if os.path.exists(filename):
            file_size = os.stat(filename).st_size
            # 录制的视频大小为0，删除文件
            if file_size == 0:
                os.remove(filename)
            # 录制到的内容是404，删除文件
            if file_size < 1024:
                with open(filename, 'r', encoding='utf-8') as f:
                    file_info = str(f.read())
                if '<head><title>404 Not Found</title></head>' in file_info:
                    os.remove(filename)


        # GUI
        if app.win_mode:
            app.win.set_state(room, '未开播', color='#000000')

        # 自动转码
        if config.is_auto_transcode():
            transcode_manager.start_transcode(filename)

        # 再次检测是否在直播，防止因网络问题造成的提前停止录制
        # 如果是主动停止录制，则不立刻再次检查
        if not rec.stop_signal:
            monitor.check_room(room)

        rec.stop()

    t = Thread(target=download)
    t.start()

    # if room.record_danmu:
    #     threading.Thread(target=partial(danmu_recorder.start_recording, room, browser, rec, filename, now)).start()
    # elif browser is not None:
    #     browser.quit()  # 关闭浏览器，清除缓存
    if browser is not None and not room.record_danmu:
        browser.quit()
