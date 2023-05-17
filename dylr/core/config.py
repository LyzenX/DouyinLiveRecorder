# coding=utf-8
"""
:author: Lyzen
:date: 2023.04.03
:brief: 配置文件读取与处理
"""

import json
import os.path

from dylr.core import record_manager, app
from dylr.core.room import Room
from dylr.util import logger, cookie_utils

configs = {
    'debug': False,
    'check_period': 30,
    'check_period_random_offset': 10,
    'important_check_period': 3,
    'important_check_period_random_offset': 3,
    'check_threads': 1,
    'check_wait': 0.5,
    'ffmpeg_path': '',
    'auto_transcode': False,
    'auto_transcode_encoder': 'copy',
    'auto_transcode_bps': '0',
    'auto_transcode_delete_origin': False,
    'download_path': 'download',
}


def read_configs():
    global configs
    logger.info('reading configs')
    with open('config.txt', 'r', encoding='UTF-8') as f:
        lines = f.readlines()
    for line in lines:
        # 去除无用行
        if line.strip().startswith('#') or '=' not in line:
            continue
        lv = line[0:line.index('=')].strip()
        rv = line[line.index('=')+1:].strip()
        # 使用了不支持的配置
        if lv not in configs:
            logger.warning_and_print(f'unsupported config {lv} = {rv}')
            continue
        # 将读取的配置字符串转为对应类型并存入 config 字典
        # 注意 bool('True') == False
        if type(configs[lv]) == bool:
            configs[lv] = True if rv.lower() == 'true' else False
        else:
            configs[lv] = type(configs[lv])(rv)
        logger.info(f'config {lv} = {rv}')


def set_config(conf: str, info):
    configs[conf] = info
    logger.info_and_print(f'set config {conf} = {info}')
    file = open('config.txt', 'r+', encoding='UTF-8')
    lines = file.readlines()
    for index, line in enumerate(lines):
        if line.startswith(conf+' =') or line.startswith(conf+'='):
            lines[index] = f'{conf} = {info}\n'
            print('found')
    file.seek(0)
    file.writelines(lines)
    file.close()


def read_rooms() -> list:
    res = []
    if not os.path.exists('rooms.json'):
        with open('rooms.json', 'w') as f:
            f.write('[]')
    with open("rooms.json", 'r', encoding='UTF-8') as f:
        info = json.load(f)
    # 记录房间是否是旧版本的，如果是，升级到新版本
    upgrade = False
    for room_json in info:
        room_id = room_json['id']
        room_name = room_json['name']
        auto_record = room_json['auto_record']
        record_danmu = room_json['record_danmu']
        if 'important' in room_json:
            important = room_json['important']
        else:
            important = False
            upgrade = True
        if 'user_sec_id' in room_json:
            user_sec_id = room_json['user_sec_id']
        else:
            user_sec_id = None
        res.append(Room(room_id, room_name, auto_record, record_danmu, important, user_sec_id))
        if not app.win_mode:
            print(f'加载房间 {room_name}({room_id})')
        logger.info(f'loaded room: {room_name}({room_id}) '
                    f'auto_record={auto_record} record_danmu={record_danmu} '
                    f'important={important} user_sec_id={user_sec_id}')
        if upgrade:
            save_rooms(res)
            logger.info(f'rooms.json 为旧版本文件，已将升级到新版本。')
    return res


def save_rooms(rooms=None):
    if rooms is None:
        rooms = record_manager.rooms
    rooms_json = []
    for room in rooms:
        rooms_json.append({
            "id": room.room_id,
            "name": room.room_name,
            "auto_record": room.auto_record,
            "record_danmu": room.record_danmu,
            "important": room.important,
            "user_sec_id": room.user_sec_id
        })
    with open("rooms.json", "w", encoding='utf-8') as f:
        json.dump(rooms_json, f, indent=2, ensure_ascii=False)


def debug():
    return configs['debug']


def get_check_period():
    return configs['check_period']


def get_check_period_random_offset():
    return configs['check_period_random_offset']


def get_important_check_period():
    return configs['important_check_period']


def get_important_check_period_random_offset():
    return configs['important_check_period_random_offset']


def get_check_threads():
    return configs['check_threads']


def get_check_wait_time():
    return configs['check_wait']


def get_ffmpeg_path():
    return configs['ffmpeg_path']


def is_auto_transcode():
    return configs['auto_transcode']


def get_auto_transcode_encoder():
    return configs['auto_transcode_encoder']


def get_auto_transcode_bps():
    return configs['auto_transcode_bps']


def is_auto_transcode_delete_origin():
    return configs['auto_transcode_delete_origin']

def get_download_path():
    return configs['download_path']
