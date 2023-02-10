# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.17
:brief: GUI中显示主播信息的网格布局
"""

import os
import subprocess
import sys
import tkinter as tk
import tkinter.messagebox
from functools import partial
from tkinter import ttk

from dylr.core import record_manager, config, monitor


class GripFrame(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text='录制列表', padding=2)

        self._get_label_bold("主播Web_Rid", 30).grid(row=0, column=0, sticky=tk.EW)
        self._get_label_bold("主播名", 50).grid(row=0, column=1, sticky=tk.EW)
        self._get_label_bold("录制状态", 50).grid(row=0, column=2, sticky=tk.EW)
        self._get_label_bold('监测直播', 20).grid(row=0, column=3, sticky=tk.EW)
        self._get_label_bold('录制弹幕', 20).grid(row=0, column=4, sticky=tk.EW)
        self._get_label_bold('重要主播', 20).grid(row=0, column=5, sticky=tk.EW)
        self._get_label_bold(' ', 80).grid(row=0, column=6, sticky=tk.EW)

        self._index = 0
        self.widgets = {}

    def append(self, web_rid, name, state, auto_record, record_danmu, important):
        self._index += 1

        label1 = self._get_label(web_rid, 20)
        label1.grid(row=self._index, column=0, sticky=tk.EW)

        label2 = self._get_label(name, 20)
        label2.grid(row=self._index, column=1, sticky=tk.EW)

        label3 = self._get_label(state, 20)
        label3.grid(row=self._index, column=2, sticky=tk.EW)

        label4 = self._get_label('是' if auto_record else '否', 50)
        label4.bind('<Double-Button-1>', func=partial(self._set_auto_record, web_rid))
        label4.grid(row=self._index, column=3, sticky=tk.EW)

        label5 = self._get_label('是' if record_danmu else '否', 50)
        label5.bind('<Double-Button-1>', func=partial(self._set_record_danmu, web_rid))
        label5.grid(row=self._index, column=4, sticky=tk.EW)

        label6 = self._get_label('是' if important else '否', 50)
        label6.bind('<Double-Button-1>', func=partial(self._set_important, web_rid))
        label6.grid(row=self._index, column=5, sticky=tk.EW)

        btn_frame = tk.Frame(self, bg='#FFFFFF', relief='ridge', borderwidth=2)
        ttk.Button(btn_frame, text='打开目录', command=partial(self._open_explorer, 'download/' + name)) \
            .grid(row=0, column=0, sticky=tk.EW)
        # ttk.Button(btn_frame, text='房间设置') \
        #     .grid(row=0, column=1, sticky=tk.EW)
        ttk.Button(btn_frame, text='移除', command=partial(self.request_remove, web_rid, name)) \
            .grid(row=0, column=1, sticky=tk.EW)
        btn_frame.grid(row=self._index, column=6, sticky=tk.EW)
        self.widgets[web_rid] = [label1, label2, label3, label4, label5, label6, btn_frame]

    def remove_all(self):
        for i in self.widgets.keys():
            self.remove(i)

    def remove(self, web_rid):
        if web_rid in self.widgets:
            lst = self.widgets[web_rid]
            for i in range(len(lst)):
                lst[i].grid_remove()

    def set(self, web_rid, text, color):
        if web_rid in self.widgets:
            self.widgets[web_rid][2].config(text=text, fg=color)

    def request_remove(self, web_rid, name):
        """ 询问是否删除，避免误删 """
        res = tk.messagebox.askokcancel('删除房间', f'确定要删除房间{name}({web_rid})吗？\n如果不想监测和录制可以将其设为不自动录制。')
        if not res:
            return
        self.remove(web_rid)
        room = record_manager.get_room(web_rid)
        if room is None:
            return
        record_manager.rooms.remove(room)
        config.save_rooms()
        recording = record_manager.get_recording(room)
        if recording is not None:
            recording.stop()

    def _set_auto_record(self, web_rid, event):
        room = record_manager.get_room(web_rid)
        if room is None:
            return
        room.auto_record = not room.auto_record
        if web_rid in self.widgets:
            self.widgets[web_rid][3].config(text='是' if room.auto_record else '否')
        config.save_rooms()

    def _set_record_danmu(self, web_rid, event):
        room = record_manager.get_room(web_rid)
        if room is None:
            return
        room.record_danmu = not room.record_danmu
        if web_rid in self.widgets:
            self.widgets[web_rid][4].config(text='是' if room.record_danmu else '否')
        config.save_rooms()

    def _set_important(self, web_rid, event):
        room = record_manager.get_room(web_rid)
        if room is None:
            return
        room.important = not room.important
        if web_rid in self.widgets:
            self.widgets[web_rid][5].config(text='是' if room.important else '否')
        config.save_rooms()

        if room.important and str(web_rid) not in monitor.important_room_threads:
            monitor.start_important_monitor_thread(room)

    def _get_label(self, text, padx):
        label = tk.Label(self, text=str(text), bg='#FFFFFF', font=('微软雅黑', 14),
                         relief='ridge', padx=padx, borderwidth=1)
        return label

    def _get_label_bold(self, text, padx):
        return tk.Label(self, text=str(text), bg='#FFFFFF', font=('微软雅黑', 16, "bold"),
                        relief='ridge', padx=padx, borderwidth=2)

    def _open_explorer(self, path: str):
        if not os.path.exists(path):
            os.mkdir(path)
        if sys.platform == 'mac':
            subprocess.call(["open", path])
        else:
            os.startfile(path.replace('/', '\\'))
