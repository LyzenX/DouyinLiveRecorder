# coding=utf-8

def move_to_screen_center(win):
    """ 把窗口移动到屏幕中间 """
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    window_size = win.geometry().split('+')[0]
    window_width, window_height = map(int, window_size.split('x'))
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    y -= 40  # 状态栏大约高度
    win.geometry('{:d}x{:d}+{:d}+{:d}'.format(
        window_width, window_height, x, y))
