# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.13
:brief: 日志工具
"""
import sys
import time
import os.path
import logging
import traceback

from dylr.core import config, app

now = time.localtime()
now_str = time.strftime('%Y%m%d_%H%M%S', now)
filename = f'./logs/{now_str}.log'
if not os.path.exists('./logs'):
    os.mkdir('./logs')
# logging.basicConfig(filename=filename,
#                     level=logging.INFO,
#                     encoding='UTF-8',
#                     format='%(asctime)s [%(levelname)s] %(message)s')
instance = logging.getLogger('Main')
instance.setLevel(logging.INFO)
handler = logging.FileHandler(filename, encoding='utf-8')
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
instance.addHandler(handler)


def log_uncaught_exceptions(ex_cls, ex, tb):
    fatal_and_print(''.join(traceback.format_tb(tb)))
    fatal_and_print('{0}: {1}'.format(ex_cls, ex))


sys.excepthook = log_uncaught_exceptions


def info_and_print(text: str):
    if not app.win_mode:
        print(text)
    info(text)


def debug_and_print(text: str):
    if config.debug():
        if not app.win_mode:
            print(text)
        debug(text)


def warning_and_print(text: str):
    if not app.win_mode:
        print(text)
    warning(text)


def error_and_print(text: str):
    if not app.win_mode:
        print(text)
    error(text)


def fatal_and_print(text: str):
    if not app.win_mode:
        print(text)
    fatal(text)


def info(text: str):
    instance.info(text)


def debug(text: str):
    instance.debug(text)


def warning(text: str):
    instance.warning(text)


def error(text: str):
    instance.error(text)


def fatal(text: str):
    instance.critical(text)
