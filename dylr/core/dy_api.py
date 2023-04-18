# coding=utf-8
"""
:author: Lyzen
:date: 2023.02.10
:brief: 抖音api
"""
import json
import random
import time

import requests

from dylr.core.room_info import RoomInfo
from dylr.util import cookie_utils, logger


def get_api_url(room_id):
    return 'https://live.douyin.com/webcast/room/web/enter/?aid=6383&live_id=1&device_platform=web&language=zh-CN' \
           '&enter_from=web_live&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN' \
           f'&browser_platform=Win32&browser_name=Chrome&browser_version=109.0.0.0&web_rid={room_id}' \
           f'&enter_source=&Room-Enter-User-Login-Ab=1&is_need_double_stream=false'


def find_stream_url(room):
    json_info = get_live_state_json(room.room_id)
    if json_info is None:
        return None
    stream_url = json_info['stream_url']['flv_pull_url']['FULL_HD1']
    return stream_url


def get_api_user_url(sec_user_id):
    # todo 使用该接口获取只有用户主页链接时的开播状态
    return f'https://webcast.huoshan.com/webcast/room/info_by_user/?sec_user_id={sec_user_id}&aid=1112'


def get_live_state_json(room_id):
    api_url = get_api_url(room_id)
    req = requests.get(api_url, headers=get_request_headers(), proxies=get_proxies())
    res = req.text
    if '系统繁忙，请稍后再试' in res:
        cookie_utils.record_cookie_failed()
    try:
        info_json = json.loads(res)
    except:
        logger.debug(f'failed to load response of GET to json when finding stream url of {room_id}, using api 1, '
                     f'response: ' + res)
        cookie_utils.record_cookie_failed()
        return None
    try:
        info_json = info_json['data']['data'][0]
    except:
        logger.debug(f'failed to load json when finding stream url of {room_id}, using api 1, '
                     f'response: ' + res)
        cookie_utils.record_cookie_failed()
        return None
    return info_json


def get_danmu_ws_url(room_id, live_room_real_id, retry=0):
    if retry >= 5:
        return f"wss://webcast3-ws-web-lf.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:{live_room_real_id}|wss_push_did:7184667748424615439|dim_log_id:2023011316221327ACACF0E44A2C0E8200|fetch_time:${int(time.time())}123|seq:1|wss_info:0-1673598133900-0-0|wrds_kvs:WebcastRoomRankMessage-1673597852921055645_WebcastRoomStatsMessage-1673598128993068211&cursor=u-1_h-1_t-1672732684536_r-1_d-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&device_platform=web&cookie_enabled=true&screen_width=1228&screen_height=691&browser_language=zh-CN&browser_platform=Mozilla&browser_name=Mozilla&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/100.0.4896.75%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id={live_room_real_id}&heartbeatDuration=0&signature=00000000"

    api = f'https://live.douyin.com/{room_id}'
    res = requests.get(api, headers=get_request_headers(), proxies=get_proxies())
    req = res.text
    index_render_data = req.find('RENDER_DATA')
    if index_render_data == -1:
        logger.warning_and_print(f"cannot find RENDER_DATA when loading {room_id}")
        cookie_utils.record_cookie_failed()
        return get_danmu_ws_url(room_id, live_room_real_id, retry+1)

    info = req[index_render_data:]
    index = info.find("user_unique_id")
    if index == -1:
        logger.warning_and_print(f"cannot find user_unique_id when loading RENDER_DATA of {room_id}")
        return get_danmu_ws_url(room_id, live_room_real_id, retry+1)

    info = info[index+14+9:]
    index = info.find("%")
    user_unique_id = info[0:index]

    return f"wss://webcast3-ws-web-lf.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:{live_room_real_id}|wss_push_did:{user_unique_id}|dim_log_id:2023011316221327ACACF0E44A2C0E8200|fetch_time:${int(time.time())}123|seq:1|wss_info:0-1673598133900-0-0|wrds_kvs:WebcastRoomRankMessage-1673597852921055645_WebcastRoomStatsMessage-1673598128993068211&cursor=u-1_h-1_t-1672732684536_r-1_d-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&device_platform=web&cookie_enabled=true&screen_width=1228&screen_height=691&browser_language=zh-CN&browser_platform=Mozilla&browser_name=Mozilla&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/100.0.4896.75%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id={live_room_real_id}&heartbeatDuration=0&signature=00000000"
    # return f"wss://webcast3-ws-web-hl.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:{live_room_real_id}|wss_push_did:7201842352902161920|dim_log_id:20230407222538FE28B78765CCB539768D|fetch_time:1680877539036|seq:1|wss_info:0-1680877539036-0-0|wrds_kvs:WebcastRoomStatsMessage-1680877533286700255_PreviewControlSyncData-1680877503878543016_WebcastRoomRankMessage-1680877275351355795&cursor=t-1680877539036_r-1_d-1_u-1_h-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&maxCacheMessageNumber=20&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&user_unique_id=7201842352902161920&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/100.0.4896.75%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id={live_room_real_id}&heartbeatDuration=0&signature=WMvK57+IuF+b/NFM"
    # return f"wss://webcast3-ws-web-lf.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:{live_room_real_id}|wss_push_did:{user_unique_id}|dim_log_id:202304090019537CDAD97C61C15213D469|fetch_time:1680970793876|seq:1|wss_info:0-1680970793876-0-0|wrds_kvs:InputPanelComponentSyncData-1680959751992084801_WebcastRoomRankMessage-1680970684111497354_WebcastRoomStatsMessage-1680970792091320480_HighlightContainerSyncData-1&cursor=d-1_u-1_h-1_t-1680970793876_r-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&maxCacheMessageNumber=20&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&user_unique_id={user_unique_id}&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/100.0.4896.75%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id={live_room_real_id}&heartbeatDuration=0&signature=00000000"


def get_request_headers():
    return {
        # 'user-agent': '"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        #               ' (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"',
        'user-agent': get_random_ua(),
        'cookie': cookie_utils.cookie_cache
    }


def is_going_on_live(room):
    room_json = get_live_state_json(room.room_id)
    if room_json is None:
        cookie_utils.record_cookie_failed()
        return False
    room_info = RoomInfo(room, room_json)
    return room_info.is_going_on_live()


def get_proxies():
    return {"http": None, "https": None}


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
