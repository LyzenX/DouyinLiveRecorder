import datetime
import time

from dylr.core import app, record_manager


class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


def get_time_str(t):
    res = ''
    seconds = t.seconds
    if seconds > 3600:
        res += f'{seconds // 3600}时'
    if seconds > 60:
        res += f'{seconds % 3600 // 60}分'
    res += f'{seconds % 60}秒'
    return res


def run():
    getch = _Getch()
    while True:
        info = getch()
        now = datetime.datetime.now()
        if info == b'l' or info == b'L':
            if not record_manager.get_recordings():
                print('没有正在录制的直播间')
                continue
            print('------- 正在录制的房间列表 -------')
            for rec in record_manager.get_recordings():
                print(f'{rec.room.room_name}({rec.room.room_id}) 已录制 {get_time_str(now - rec.start_time)}')
            print('------------------------------')
        if info == b'\x03':
            app.stop_all_threads = True
            print('捕捉到Ctrl+C，关闭L键功能，尝试关闭软件')
            break
        if app.stop_all_threads:
            break
