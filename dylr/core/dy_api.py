# coding=utf-8
"""
:author: Lyzen
:date: 2023.02.10
:brief: 抖音api
"""
import json
import random
import urllib.parse

import requests

from dylr.util import cookie_utils, logger


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


def find_stream_url2(room):
    json_info = get_live_state_json(room.room_id)
    if json_info is None:
        return None
    stream_url = json_info['stream_url']['flv_pull_url']['FULL_HD1']
    return stream_url


def get_api_user_url(sec_user_id):
    # todo 使用该接口获取只有用户主页链接时的开播状态
    return f'https://webcast.huoshan.com/webcast/room/info_by_user/?sec_user_id={sec_user_id}&aid=1112'


def get_live_state_json(room_id):
    api = f'https://live.douyin.com/{room_id}'
    proxies = {"http": None, "https": None}
    res = requests.get(api, headers=get_request_headers(), proxies=proxies)
    req = res.text
    index_render_data = req.find('RENDER_DATA')
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
        try:
            room_info_json = info_json['app']['initialState']['roomStore']['roomInfo']['room']
        except:
            logger.warning("Failed to load json while decoding json got from api2. json: "+str(info_json))
            cookie_utils.record_cookie_failed()
            return None

        # 获取成功，清除 cookie 失败次数
        cookie_utils.cookie_failed = 0

        return room_info_json
    return None


def get_request_headers():
    return {
        # 'user-agent': '"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        #               ' (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"',
        'user-agent': get_random_ua(),
        'cookie': cookie_utils.cookie_cache
    }


def get_random_ua():
    os_list = ['(Windows NT 10.0; WOW64)', '(Windows NT 10.0; WOW64)', '(Windows NT 10.0; Win64; x64)',
               '(Windows NT 6.3; WOW64)', '(Windows NT 6.3; Win64; x64)',
               '(Windows NT 6.1; Win64; x64)', '(Windows NT 6.1; WOW64)',
               '(X11; Linux x86_64)',
               '(Macintosh; Intel Mac OS X 10_12_6)']
    # chrome版本(均为真实存在的发布版本)
    chrome_version_list = ['110.0.5481.77', '110.0.5481.30', '109.0.5414.74', '108.0.5359.71', '108.0.5359.22',
                           '107.0.5304.62', '107.0.5304.18', '106.0.5249.61', '106.0.5249.21', '105.0.5195.52',
                           '105.0.5195.19', '104.0.5112.79', '104.0.5112.29', '104.0.5112.20', '103.0.5060.134',
                           '103.0.5060.53', '103.0.5060.24', '102.0.5005.61', '102.0.5005.27', '101.0.4951.41',
                           '101.0.4951.15', '100.0.4896.60', '100.0.4896.20', '99.0.4844.51', '99.0.4844.35',
                           '99.0.4844.17', '98.0.4758.102', '98.0.4758.80', '98.0.4758.48', '97.0.4692.71']
    return f'"Mozilla/5.0 {random.choice(os_list)} AppleWebKit/537.36 (KHTML, like Gecko) ' \
           f'Chrome/{random.choice(chrome_version_list)} Safari/537.36"'
