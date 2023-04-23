# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 录制管理
"""
from dylr.core.recording import Recording
from dylr.util import logger

rooms = []
recordings = []


def get_rooms() -> list:
    return rooms


def get_auto_record_rooms() -> list:
    return [room for room in rooms if room.auto_record and '将会在开播时获取' not in str(room.room_id)]


def get_monitor_rooms() -> list:
    res = [room for room in rooms if room.auto_record and not room.important and '将会在开播时获取' not in str(room.room_id)]
    for rec in recordings:
        if rec.room in res:
            res.remove(rec.room)
    return res


def get_room_without_web_rid() -> list:
    return [room for room in rooms if room.auto_record and '将会在开播时获取' in str(room.room_id)]


def get_important_rooms() -> list:
    return [room for room in rooms if room.important and '将会在开播时获取' not in str(room.room_id)]


def get_recordings() -> list:
    return recordings


def get_recording(room):
    for rec in recordings:
        if rec.room == room:
            return rec
    return None


def is_recording(room) -> bool:
    return get_recording(room) is not None


def start_recording(room, room_info):
    if is_recording(room):
        logger.warning_and_print(f'{room.room_name}({room.room_id}) 已经在录制了')
        return
    recording = Recording(room, room_info)
    recording.start()
    recordings.append(recording)


def get_room(room_id):
    for room in rooms:
        if room.room_id == room_id:
            return room
    return None
