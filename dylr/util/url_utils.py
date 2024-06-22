# 代码来源：https://github.com/biliup/biliup

import hashlib
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode


def get_ms_stub(live_room_real_id, user_unique_id):
    params = {
        "live_id": "1",
        "aid": "6383",
        "version_code": 180800,
        "webcast_sdk_version": '1.0.14-beta.0',
        "room_id": live_room_real_id,
        "sub_room_id": "",
        "sub_channel_id": "",
        "did_rule": "3",
        "user_unique_id": user_unique_id,
        "device_platform": "web",
        "device_type": "",
        "ac": "",
        "identity": "audience"
    }
    sig_params = ','.join([f'{k}={v}' for k, v in params.items()])
    return hashlib.md5(sig_params.encode()).hexdigest()


def build_request_url(url: str, user_agent: str) -> str:
    parsed_url = urlparse(url)
    existing_params = parse_qs(parsed_url.query)
    existing_params['aid'] = ['6383']
    existing_params['device_platform'] = ['web']
    existing_params['browser_language'] = ['zh-CN']
    existing_params['browser_platform'] = ['Win32']
    existing_params['browser_name'] = [user_agent.split('/')[0]]
    existing_params['browser_version'] = [
        user_agent.split(existing_params['browser_name'][0])[-1][1:]]
    new_query_string = urlencode(existing_params, doseq=True)
    new_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query_string,
        parsed_url.fragment
    ))
    return new_url