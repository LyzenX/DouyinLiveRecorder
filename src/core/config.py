# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 配置文件读取与处理
"""

import json
import os.path

from src.core import app, record_manager
from src.core.room import Room
from src.util import logger, cookie_utils

configs = {
    'debug': False,
    'check_period': 30,
    'check_threads': 2,
    'monitor_using_api': False,
    'ffmpeg_path': '',
    'auto_transcode': False,
    'auto_transcode_encoder': 'copy',
    'auto_transcode_bps': '0',
    'auto_transcode_delete_origin': False,
    'cookie': ''
}


def read_configs():
    logger.info('reading configs')
    global configs
    with open('config.txt', 'r', encoding='UTF-8') as f:
        lines = f.readlines()
    for line in lines:
        if line.strip().startswith('#'):
            continue
        if '=' in line:
            lv = line[0:line.index('=')].strip()
            rv = line[line.index('=')+1:].strip()
            if lv in configs:
                if type(configs[lv]) == bool:
                    configs[lv] = True if rv.lower() == 'true' else False
                else:
                    configs[lv] = type(configs[lv])(rv)
                if lv != 'cookie':
                    logger.info(f'config {lv} = {rv}')
                elif len(rv) > 50:
                    cookie_utils.cookie_cache = rv
                    logger.info('using custom cookie')


def read_rooms() -> list:
    res = []
    if not os.path.exists('rooms.json'):
        with open('rooms.json', 'w') as f:
            f.write('[]')
    with open("rooms.json", 'r', encoding='UTF-8') as f:
        info = json.load(f)
        for room_json in info:
            room_id = room_json['id']
            room_name = room_json['name']
            auto_record = room_json['auto_record']
            record_danmu = room_json['record_danmu']
            res.append(Room(room_id, room_name, auto_record, record_danmu))
            if not app.win_mode:
                print(f'加载房间 {room_name}({room_id})')
            logger.info(f'loaded room: {room_name}({room_id}) auto_record={auto_record} record_danmu={record_danmu}')
    return res


def save_rooms():
    rooms_json = []
    for room in record_manager.rooms:
        rooms_json.append({
            "id": room.room_id,
            "name": room.room_name,
            "auto_record": room.auto_record,
            "record_danmu": room.record_danmu
        })
    with open("rooms.json", "w", encoding='utf-8') as f:
        json.dump(rooms_json, f, indent=2, ensure_ascii=False)


def debug():
    return configs['debug']


def get_check_period():
    return configs['check_period']


def get_check_threads():
    return configs['check_threads']


def get_custom_cookie():
    return configs['cookie']


def is_using_custom_cookie():
    return len(get_custom_cookie()) > 50


def is_monitor_using_api():
    return configs['monitor_using_api']


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
