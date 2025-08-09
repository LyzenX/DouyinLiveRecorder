# coding=utf-8
"""
:author: Lyzen
:date: 2023.02.10
:brief: 抖音api
"""
import json
import random
import time

import jsengine
import requests

from dylr.core.room_info import RoomInfo
from dylr.util import cookie_utils, logger, url_utils


def get_api_url(room_id):
    return 'https://live.douyin.com/webcast/room/web/enter/?aid=6383&live_id=1&device_platform=web&language=zh-CN' \
           '&enter_from=web_live&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN' \
           f'&browser_platform=Win32&browser_name=Chrome&browser_version=109.0.0.0&web_rid={room_id}' \
           f'&enter_source=&Room-Enter-User-Login-Ab=1&is_need_double_stream=false&a_bogus=0'


def find_stream_url(room):
    json_info = get_live_state_json(room.room_id)
    if json_info is None:
        return None
    stream_url = json_info['stream_url']['flv_pull_url']['FULL_HD1']
    return stream_url


def get_live_state_json(room_id):
    api_url = get_api_url(room_id)
    req = requests.get(api_url, headers=get_request_headers(), proxies=get_proxies())
    res = req.text
    if '系统繁忙，请稍后再试' in res:
        cookie_utils.record_cookie_failed()
    try:
        info_json = json.loads(res)
    except:
        logger.debug(f'failed to load response of GET to json when searching stream url of {room_id}, using api 1, '
                     f'response: ' + res)
        cookie_utils.record_cookie_failed()
        return None
    try:
        info_json = info_json['data']['data'][0]
    except:
        logger.debug(f'failed to load json when searching stream url of {room_id}, using api 1, '
                     f'response: ' + res)
        cookie_utils.record_cookie_failed()
        return None
    return info_json


def get_danmu_ws_url(room_id, live_room_real_id, retry=0):
    # 2024.6.20 接口更新，需要signature参数
    # 代码来源：https://github.com/biliup/biliup/blob/master/biliup/Danmaku/douyin_util/__init__.py
    user_unique_id = random.randint(7300000000000000000, 7999999999999999999)

    with open(r'dylr/util/webmssdk.js', 'r', encoding='utf-8') as f:
        js_enc = f.read()

    ua = get_request_headers()['user-agent']

    ctx = jsengine.jsengine()
    js_dom = f"""
document = {{}}
window = {{}}
navigator = {{
  'userAgent': '{ua}'
}}
""".strip()
    final_js = js_dom + js_enc
    ctx.eval(final_js)
    function_caller = f"get_sign('{url_utils.get_ms_stub(live_room_real_id, user_unique_id)}')"
    signature = ctx.eval(function_caller)

    webcast5_params = {
        "room_id": live_room_real_id,
        "compress": 'gzip',
        "version_code": 180800,
        "webcast_sdk_version": '1.0.14-beta.0',
        "live_id": "1",
        "did_rule": "3",
        "user_unique_id": user_unique_id,
        "identity": "audience",
        "signature": signature,
    }
    uri = url_utils.build_request_url(
        f"wss://webcast5-ws-web-lf.douyin.com/webcast/im/push/v2/?{'&'.join([f'{k}={v}' for k, v in webcast5_params.items()])}",
        ua)

    return uri
    # return f"wss://webcast3-ws-web-lf.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:{live_room_real_id}|wss_push_did:7184667748424615439|dim_log_id:2023011316221327ACACF0E44A2C0E8200|fetch_time:${int(time.time())}123|seq:1|wss_info:0-1673598133900-0-0|wrds_kvs:WebcastRoomRankMessage-1673597852921055645_WebcastRoomStatsMessage-1673598128993068211&cursor=u-1_h-1_t-1672732684536_r-1_d-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&device_platform=web&cookie_enabled=true&screen_width=1228&screen_height=691&browser_language=zh-CN&browser_platform=Mozilla&browser_name=Mozilla&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/100.0.4896.75%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id={live_room_real_id}&heartbeatDuration=0&signature=00000000"
    # return f"wss://webcast3-ws-web-lf.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:{live_room_real_id}|wss_push_did:{user_unique_id}|dim_log_id:2023011316221327ACACF0E44A2C0E8200|fetch_time:${int(time.time())}123|seq:1|wss_info:0-1673598133900-0-0|wrds_kvs:WebcastRoomRankMessage-1673597852921055645_WebcastRoomStatsMessage-1673598128993068211&cursor=u-1_h-1_t-1672732684536_r-1_d-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&device_platform=web&cookie_enabled=true&screen_width=1228&screen_height=691&browser_language=zh-CN&browser_platform=Mozilla&browser_name=Mozilla&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/100.0.4896.75%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id={live_room_real_id}&heartbeatDuration=0&signature=00000000"


def get_web_rid_from_short_url(url: str):
    resp = requests.head(url, headers=get_request_headers(), proxies=get_proxies())
    full_uri = resp.headers.get('location')
    room_id = full_uri[full_uri.index('reflow/') + 7:full_uri.index('?')]
    api = f'https://webcast.amemv.com/webcast/room/reflow/info/?type_id=0&live_id=1&room_id={room_id}&app_id=1128'
    resp = requests.get(api, headers=get_request_headers(), proxies=get_proxies())
    json_root = json.loads(resp.text)
    return json_root['data']['room']['owner']['web_rid']


def get_api_user_url(sec_user_id):
    # 使用该接口获取只有用户主页链接时的开播状态，目前已失效
    return f'https://webcast.huoshan.com/webcast/room/info_by_user/?sec_user_id={sec_user_id}&aid=1112'


def get_user_info(sec_user_id):
    ms_token = generate_random_str(132)
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        'referer': 'https://www.douyin.com/',
        'accept-encoding': None,
        'Cookie': cookie_utils.cookie_cache + '; msToken=' + ms_token + '; odin_tt=324fb4ea4a89c0c05827e18a1ed9cf9bf8a17f7705fcc793fec935b637867e2a5a9b8168c885554d029919117a18ba69; passport_csrf_token=f61602fc63757ae0e4fd9d6bdcee4810;'
    }
    prefix = 'https://www.douyin.com/aweme/v1/web/aweme/post/?'
    query = f'device_platform=webapp&aid=6383&channel=channel_pc_web&sec_user_id={sec_user_id}&max_cursor=0&locate_query=false&show_live_replay_strategy=1&count=1&publish_video_strategy_type=2&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Chrome&browser_version=100.0.4896.75&browser_online=true&engine_name=Blink&engine_version=100.0.4896.75&os_name=Windows&os_version=10&cpu_core_num=12&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=0&webid=7201842352902161920&msToken={ms_token}'
    response = json.loads(requests.post(
        "http://47.115.208.101:9090/xb", data={"param": query}, headers=headers).text)
    params = response["param"]
    resp = requests.get(prefix + params,
                        headers=headers, proxies=get_proxies())
    nickname_index = resp.text.find('nickname')
    if nickname_index == -1:
        return None, None
    nickname = resp.text[nickname_index + 11:]
    nickname = nickname[:nickname.find('"')]

    web_rid_index = resp.text.find('web_rid')
    if web_rid_index != -1:
        web_rid = resp.text[web_rid_index + 12:]
        web_rid = web_rid[:web_rid.find('\\"')]
        return nickname, web_rid
    else:
        return nickname, None


def get_request_headers():
    return {
        # 'user-agent': '"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        #               ' (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"',
        'user-agent': get_random_ua(),
        'cookie': cookie_utils.cookie_cache
    }


def generate_random_str(randomlength):
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789='
    length = len(base_str) - 1
    for _ in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str


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
