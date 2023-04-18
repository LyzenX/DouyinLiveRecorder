import threading
import time
import traceback
from typing import Optional

from dylr.plugin import plugin
from dylr.core import dy_api, record_manager
from dylr.core.danmu_recorder import DanmuRecorder
from dylr.core.room import Room
from dylr.core.room_info import RoomInfo
from dylr.core.video_recorder import VideoRecorder
from dylr.util import cookie_utils, logger


class Recording:
    def __init__(self, room: Room, room_info: Optional[RoomInfo] = None):
        self.room = room
        self.room_info = room_info
        self.video_recorder = None
        self.danmu_recorder = None

    def start(self):
        if self.room_info is None:
            room_json = dy_api.get_live_state_json(self.room.room_id)
            if room_json is None:
                cookie_utils.record_cookie_failed()
                return False
            self.room_info = RoomInfo(self.room, room_json)
        if not self.room_info.is_going_on_live():
            return False

        now = time.localtime()
        now_str = time.strftime('%Y%m%d_%H%M%S', now)
        video_filename = f"download/{self.room.room_name}/{now_str}.flv"

        try:
            plugin.on_live_start(self.room, video_filename)
        except:
            traceback.print_exc()
        self.start_recording_video(video_filename)
        if self.room.record_danmu:
            self.start_recording_danmu(now)
        return True

    def refresh_video_recorder(self):
        """ 再次检查是否在直播，防止因为主播网络问题而造成断录 """
        room_json = dy_api.get_live_state_json(self.room.room_id)
        if room_json is None:
            cookie_utils.record_cookie_failed()
            record_manager.recordings.remove(self)
            return False
        self.room_info = RoomInfo(self.room, room_json)
        if not self.room_info.is_going_on_live():
            record_manager.recordings.remove(self)
            return False
        now = time.localtime()
        now_str = time.strftime('%Y%m%d_%H%M%S', now)
        video_filename = f"download/{self.room.room_name}/{now_str}.flv"
        self.video_recorder = None
        logger.info_and_print(f'检测到 {self.room.room_name}({self.room.room_id}) 未下播，继续录制')
        self.start_recording_video(video_filename)

    def start_recording_video(self, filename):
        if self.video_recorder is not None:
            return
        self.video_recorder = VideoRecorder(self.room, self.room_info, self)
        threading.Thread(target=self.video_recorder.start_recording, args=(filename,)).start()

    def start_recording_danmu(self, start_time):
        if self.danmu_recorder is not None:
            return
        self.danmu_recorder = DanmuRecorder(self.room, self.room_info.get_real_room_id(), start_time)
        t = threading.Thread(target=self.danmu_recorder.start)
        t.setDaemon(True)
        t.start()

    def stop_recording_video(self):
        if self.video_recorder is None:
            return
        self.video_recorder.stop()

    def stop_recording_danmu(self):
        if self.danmu_recorder is None:
            return
