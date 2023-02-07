# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 录制器核心
"""

import json
import time
import os.path
import urllib.parse
from threading import Thread

import requests
from requests.adapters import HTTPAdapter

from dylr.core import app, config, monitor, record_manager, transcode_manager
from dylr.core.recording import Recording
from dylr.plugin import plugin
from dylr.util import logger, cookie_utils


def start_recording(room, browser=None, filename=None, stream_url=None):
    """ 启动录制 """
    if filename is None:
        now = time.localtime()
        now_str = time.strftime('%Y%m%d_%H%M%S', now)
        filename = f"download/{room.room_name}/{now_str}.flv"

    # 获取直播视频流链接
    if stream_url is None:
        stream_url = find_stream_url2(room)
        if stream_url is not None:
            logger.debug(f'find stream url of {room.room_name}({room.room_id}): {stream_url}. Starting downloading...')
        else:
            logger.error_and_print(f'{room.room_name}({room.room_id}) 获取直播资源链接失败')
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
                return
            try:
                downloading = s.get(
                    stream_url, timeout=(5, 10), verify=False, stream=True
                )
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                logger.error_and_print(f'{room.room_name}({room.room_id})直播获取超时，正在重试({retry})')
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
                            logger.info_and_print(f'主动停止{room.room_name}({room.room_id})的录制')
                            break
            except requests.exceptions.ConnectionError:
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

        rec.stop()

        # 再次检测是否在直播，防止因网络问题造成的提前停止录制
        # 如果是主动停止录制，则不立刻再次检查
        if rec.stop_signal:
            monitor.check_room(room)

    t = Thread(target=download)
    t.start()

    # if room.record_danmu:
    #     threading.Thread(target=partial(danmu_recorder.start_recording, room, browser, rec, filename, now)).start()
    # elif browser is not None:
    #     browser.quit()  # 关闭浏览器，清除缓存
    if browser is not None and not room.record_danmu:
        browser.quit()


def find_stream_url2(room):
    json_info = get_live_state_json(room.room_id)
    stream_url = json_info['stream_url']['flv_pull_url']['FULL_HD1']
    return stream_url


def find_stream_url(room):
    """ api 1 暂时失效 """
    room_id = room.room_id

    url = get_api_url1(room_id)
    proxies = {"http": None, "https": None}
    resp = requests.get(url, headers=get_request_headers(), proxies=proxies)
    resp_text = resp.text

    if '系统繁忙，请稍后再试' in resp_text:
        cookie_utils.record_cookie_failed()

    # 可能是双引号被替换成了单引号，但 json 接受双引号，故将单引号转为双引号
    resp_text = resp_text.replace("'", '"')

    try:
        json_info = json.loads(resp_text)
    except:
        logger.debug(f'failed to load response of GET to json when finding stream url of {room.room_name}({room_id}).'
                     f' response: ' + resp_text)
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


def get_api_url1(room_id):
    """ api 1 暂时失效 """
    return "https://live.douyin.com/webcast/web/enter/?aid=6383&live_id=1&device_platform=web" \
           "&language=zh-CN&enter_from=web_live&cookie_enabled=true&screen_width=1536&screen_height=864" \
           "&browser_language=zh-CN&browser_platform=Win32&browser_name=Chrome&browser_version=94.0.4606.81" \
           f"&room_id_str=&enter_source=&web_rid={room_id}"


def get_api_user_url(sec_user_id):
    # todo 使用该接口获取只有用户主页链接时的开播状态
    return f'https://webcast.huoshan.com/webcast/room/info_by_user/?sec_user_id={sec_user_id}&aid=1112'


def get_live_state_json(room_id):
    api = f'https://live.douyin.com/{room_id}'
    res = requests.get(api, headers=get_request_headers())
    req = res.text
    index_render_data = req.index('RENDER_DATA')
    if index_render_data > -1:
        info = req[index_render_data:]
        info = info[info.index('>') + 1:]
        info = info[:info.index('</script>')]
        info = urllib.parse.unquote(info)
        info = info.replace("'", '"')
        try:
            info_json = json.loads(info)
        except:
            logger.debug(f'failed to load response of GET to json when finding stream url of {room_id}, using api 2, '
                         f'response: ' + info)
            return None
        room_info_json = info_json['app']['initialState']['roomStore']['roomInfo']['room']
        return room_info_json
    else:
        cookie_utils.record_cookie_failed()
    return None


def get_request_headers():
    return {
        'user-agent': '"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                      ' (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"',
        'cookie': cookie_utils.cookie_cache
    }
