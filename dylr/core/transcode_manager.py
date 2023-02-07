# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.16
:brief: 转码
"""

import os
import subprocess
import threading
from threading import Thread

from dylr.core import config
from dylr.util import logger
from dylr.util.ffmpeg_utils import FFMpegUtils


# 同时只能有一个项目在转码，防止资源占用过高
lock = threading.Lock()


def start_transcode(filename: str):
    logger.info_and_print(f'已将 {filename} 加入转码队列')
    t = Thread(target=transcode, args=(filename,))
    t.start()


def transcode(filename: str):
    lock.acquire()

    if not ffmpeg_bin_exist():
        logger.error_and_print(f'没有找到ffmpeg可执行文件，无法转码。')
        lock.release()
        return

    logger.info_and_print(f'开始对 {filename} 转码')
    ffmpeg = FFMpegUtils()
    ffmpeg.input_file(filename)
    output_name = filename[0:filename.rindex('.')] + '.mp4'
    ffmpeg.set_output_name(output_name)
    ffmpeg.force_override()
    ffmpeg.set_video_codec(config.get_auto_transcode_encoder())
    if len(config.get_auto_transcode_bps()) > 0:
        ffmpeg.set_bit_rate(config.get_auto_transcode_bps())
    ffmpeg.set_audio_codec('copy')
    command = ffmpeg.generate()
    if len(config.get_ffmpeg_path()) > 0:
        command = config.get_ffmpeg_path() + '/' + command
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if config.is_auto_transcode_delete_origin():
        os.remove(filename)
    logger.info_and_print(f'{output_name} 转码完成')

    lock.release()


def ffmpeg_bin_exist():
    if len(config.get_ffmpeg_path()) > 0:
        ffmpeg_cmd = config.get_ffmpeg_path() + "/ffmpeg -version"
    else:
        ffmpeg_cmd = "ffmpeg -version"
    r = subprocess.run(ffmpeg_cmd, capture_output=True)
    info = str(r.stderr, "UTF-8")
    return 'version' in info
