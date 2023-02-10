# coding=utf-8
"""
:author: Lyzen
:date: 2023.01.12
:brief: 命令行 ffmpeg 小工具，用于生成 ffmpeg 指令，仅封装本人常用操作，非通用模块
"""


class VideoFilter:
    """
    视频滤镜
    """
    def __init__(self):
        self._scale_width = None
        self._scale_height = None
        self._fps = None
        self._pad_width = None
        self._pad_height = None
        self._pad_x = None
        self._pad_y = None
        self._pad_bg_color = None
        self._ass = None

    def set_scale(self, width, height):
        """
        将视频画面拉伸
        可以等比例扩大或缩小来修改分辨率
        如 1280x720 -> 1920x1080

        如果不是等比例拉伸，则画面会变形
        如果您不想让画面变形，而是给视频多出来的两边加上黑边，可以考虑使用resize_with_black_bar(width, height)

        :param width: 拉伸后的视频宽度
        :param height: 拉伸后的视频高度
        """
        self._scale_width = width
        self._scale_height = height

    def set_fps(self, fps):
        """
        设置视频帧率(如果不设置视频输出帧率，则不影响视频元数据中的帧率)
        比如视频输出帧率是15，fps滤镜是5，则视频观感是5fps，但视频元数据中仍为15fps
        :param fps:
        """
        self._fps = fps

    def set_pad(self, width, height, x, y, color: str = "black"):
        """
        将视频放于一个指定分辨率的的画布中
        坐标系为图像坐标系，即x轴从左到右、y轴从上到下为正方向
        比如将一个1080x1920的竖屏视频缩放并在两边加上黑边，变成一个1920x1080的横屏视频，则可以：
        set_scale(607, 1080)
        set_pad(1920, 1080, 656, 0)

        你可以使用resize_with_black_bar(width, height)来自动计算缩放的大小和x和y轴坐标，以便视频居中放置且不裁切不变形

        :param width: 新画布的宽度
        :param height: 新画布的高度
        :param x: 将原图像置于新位置的x轴坐标
        :param y:将原图像置于新位置的y轴坐标
        :param color: 底色，默认为黑色
        """
        self._pad_width = width
        self._pad_height = height
        self._pad_x = x
        self._pad_y = y
        self._pad_bg_color = color

    def resize_with_black_bar(self, width: int, height: int):
        """
        将视频输出为一个新的分辨率，且不对视频进行拉伸，也不对视频进行裁切
        会对视频缩放，并在多出来的部分使用黑边填充
        :param width: 输出视频的宽度
        :param height: 输出视频的高度

        python描述：

        crr = width_output / height_output  # 目标长宽比
        if width_input / height_input > crr:
            # 宽过长，上下加黑边
            # 先计算出缩放后的分辨率，由于是上下加黑边，左右即视频宽要缩放至与目标一致
            scale_ratio = width_output / width_input
            scale_width = width_output
            scale_height = int(height_input * scale_ratio)
            # 在黑色底，将视频居中放置，则视频左上角的位置应该在(0, y)
            # y是黑边总高度的一半
            x = 0
            y = (height_output - scale_height) // 2
        else:
            # 高过长，左右加黑边
            # 先计算出缩放后的分辨率，由于是左右加黑边，上下即视频高要缩放至与目标一致
            scale_ratio = height_output / height_input
            scale_width = int(width_input * scale_ratio)
            scale_height = height_output
            # 在黑色底，将视频居中放置，则视频左上角的位置应该在(x, 0)
            # x是黑边总长度的一半
            x = (width_output - scale_width) // 2
            y = 0
        self.set_scale(scale_width, scale_height)
        self.set_pad(width_output, height_output, x, y)
        """
        self.set_scale(fr"'if(gte(iw/ih\,{width}/{height})\,{width}\,ceil({height}/ih*iw/2)*2)'",
                       fr"'if(gte(iw/ih\,{width}/{height})\,ceil({width}/iw*ih/2)*2\,{height})'")
        self.set_pad(width, height,
                     fr"'if(gte(iw/ih\,{width}/{height})\,0\,({width}-({height}/ih*iw))/2)'",
                     fr"'if(gte(iw/ih\,{width}/{height})\,({height}-({width}/iw*ih))/2,0)'")

    def set_ass(self, file):
        """
        设置 ass 字幕
        :param file:
        """
        self._ass = file

    def generate(self) -> str:
        res = ''
        if self._scale_width is not None and self._scale_height is not None:
            res += f'scale={self._scale_width}:{self._scale_height},'
        if self._fps is not None:
            res += f'fps={self._fps},'
        if self._pad_width is not None and \
           self._pad_height is not None and \
           self._pad_x is not None and \
           self._pad_y is not None and \
           self._pad_bg_color is not None:
            res += f'pad={self._pad_width}:{self._pad_height}:{self._pad_x}:{self._pad_y}:{self._pad_bg_color},'
        if self._ass is not None:
            res += f"ass='{self._ass}'"

        if res != '':
            res = res.strip(',')  # 去掉最后的逗号(不一定有逗号)
        return res


class AudioFilter:
    """
    声音滤镜
    """
    def __init__(self):
        self._volume = None
        self._loudnorm = None

    def set_volume(self, value):
        """
        设置音量
        :param value:
        """
        self._volume = value

    def set_loud_norm(self, value):
        """
        统一音量
        :param value:
        """
        self._loudnorm = value

    def generate(self) -> str:
        res = ''
        if self._volume is not None:
            res += f'volume={self._volume},'
        if self._loudnorm is not None:
            res += f'loudnorm=i={self._loudnorm},'

        if res != '':
            res = res.strip(',')  # 去掉最后的逗号(不一定有逗号)
        return res


class FFMpegUtils:
    def __init__(self):
        self._video_filter = VideoFilter()
        self._audio_filter = AudioFilter()
        self._concat_mode: bool = False
        self._filelist_mode: bool = False
        self._filelist_name = None
        self._input: list = []
        self._input_fps = None
        self._output_fps = None
        self._ss = None
        self._t = None
        self._override = False
        self._output_name = None
        self._codec = None
        self._video_codec = None
        self._audio_codec = None
        self._bit_rate = None
        self._video_bit_rate = None
        self._audio_bit_rate = None
        self._audio_sampling_rate = None
        self._no_video = False
        self._no_audio = False

    def input_file(self, file):
        """
        设置输入文件
        :param file:
        """
        self._input.append(file)

    def set_output_name(self, name):
        """
        设置输出文件名
        :param name:
        """
        self._output_name = name

    def set_concat_mode(self):
        """
        设置拼接模式，可将多个文件拼接在一起
        设置该模式后，只能选择一个-i，不能同时选择视频和音频
        """
        self._concat_mode = True

    def set_filelist_mode(self, filelist_name: str = 'filelist.txt'):
        """
        设置拼接的输入文件从filelist.txt中读取
        因为纯concat模式可能不会加载所有文件
        开启filelist mode后，自动开启concat mode
        :param filelist_name 从哪个文件中读取视频列表，默认为 filelist.txt
        """
        self._concat_mode = True
        self._filelist_mode = True
        self._filelist_name = filelist_name

    def set_input_fps(self, fps: float):
        """
        设置读取的输入帧数
        影响输出的速度和持续时间而不是影响输出的帧率
        比如原视频是15fps，输入帧率为30，则读取的视频为原视频的2倍速
        :param fps:
        """
        self._input_fps = fps

    def set_output_fps(self, fps: float):
        """
        设置输出视频的帧数
        :param fps:
        """
        self._output_fps = fps

    def set_codec(self, codec):
        """
        设置编码器
        :param codec:
        """
        self._codec = codec

    def set_video_codec(self, codec):
        """
        设置视频编码器
        :param codec:
        """
        self._video_codec = codec

    def set_audio_codec(self, codec):
        """
        设置音频编码器
        :param codec:
        """
        self._audio_codec = codec

    def set_bit_rate(self, value):
        """
        设置比特率
        :param value:
        """
        self._bit_rate = value

    def set_video_bit_rate(self, value):
        """
        设置视频比特率
        :param value:
        """
        self._video_bit_rate = value

    def set_audio_bit_rate(self, value):
        """
        设置音频比特率
        :param value:
        """
        self._audio_bit_rate = value

    def set_audio_sampling_rate(self, value):
        """
        设置音频采样率
        :param value:
        """
        self._audio_sampling_rate = value

    def force_override(self):
        """
        强制覆盖输出文件
        """
        self._override = True

    def set_no_video(self):
        """
        去除视频
        """
        self._no_video = True

    def set_no_audio(self):
        """
        去除音频
        """
        self._no_audio = True

    def video_filters(self) -> VideoFilter:
        """
        设置视频滤镜
        """
        return self._video_filter

    def audio_filters(self) -> AudioFilter:
        """
        设置视频滤镜
        """
        return self._audio_filter

    def set_start_time(self, t):
        """
        设置读取视频的开始时间
        :param t:
        """
        self._ss = t

    def set_last_time(self, t):
        """
        设置读取视频的持续时间
        :param t:
        :return:
        """
        self._t = t

    def generate(self) -> str:
        """
        生成命令行指令
        """
        res = 'ffmpeg '
        # input fps
        if self._input_fps is not None:
            res += f'-r {self._input_fps} '
        # input files
        if not self._filelist_mode and not self._input:
            raise Exception('缺少输入文件')
        if self._concat_mode:
            if self._filelist_mode:
                res += f'-f concat -i "{self._filelist_name}" '
            else:
                res += '-i "concat:'
                for i in self._input:
                    res += f"'{i}'|"
                res = res.strip('|') + '" '
        else:
            for file in self._input:
                res += f'-i "{file}" '
        # codec
        if self._codec is not None:
            res += f'-c {self._codec} '
        if self._video_codec is not None:
            res += f'-c:v {self._video_codec} '
        if self._audio_codec is not None:
            res += f'-c:a {self._audio_codec} '
        # bit rate
        if self._bit_rate is not None:
            res += f'-b {self._bit_rate} '
        if self._video_bit_rate is not None:
            res += f'-b:v {self._video_bit_rate} '
        if self._audio_bit_rate is not None:
            res += f'-b:a {self._audio_bit_rate} '
        # audio sampling rate
        if self._audio_sampling_rate is not None:
            res += f'-ar {self._audio_sampling_rate} '
        # -ss and -t
        if self._ss is not None:
            res += f'-ss {self._ss} '
        if self._t is not None:
            res += f'-t {self._t} '
        # video filter
        vf = self.video_filters().generate()
        if vf != '':
            res += f'-vf "{vf}" '
        # audio filter
        af = self.audio_filters().generate()
        if af != '':
            res += f'-af "{af}" '
        # output fps
        if self._output_fps is not None:
            res += f'-r {self._output_fps} '
        # override
        if self._override:
            res += '-y '
        # no video or audio
        if self._no_video:
            res += '-vn '
        if self._no_audio:
            res += '-an '
        # output file
        if self._output_name is None:
            raise Exception('未设置输出文件名')
        res += self._output_name

        return res
