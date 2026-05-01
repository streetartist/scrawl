"""
音频系统 - 参考 Godot 的音频节点。

提供:
- AudioPlayer: 全局音频播放器（BGM、音效）
- AudioPlayer2D: 2D 空间音频（随距离衰减）
"""

from typing import Optional, Dict, List
from .node import Node, Node2D
from .math_utils import Vector2
from .signals import Signal


class AudioStream:
    """音频流资源 - 参考 Godot AudioStream。

    代表一个可播放的音频资源。
    """

    def __init__(self, path: str = ""):
        self.path = path
        self.loop = False
        self.loop_offset = 0.0
        self._duration = 0.0

    @property
    def duration(self) -> float:
        return self._duration


class AudioBus:
    """音频总线 - 用于分组控制音量。"""

    def __init__(self, name: str = "Master"):
        self.name = name
        self.volume_db = 0.0
        self.mute = False
        self.solo = False


class AudioPlayer(Node):
    """全局音频播放器 - 参考 Godot AudioStreamPlayer。

    不受空间距离影响的音频播放器，适用于 BGM 和全局音效。

    用法:
        bgm = AudioPlayer("BGM")
        bgm.stream = AudioStream("music/background.ogg")
        bgm.volume_db = -10
        bgm.play()

        sfx = AudioPlayer("SFX")
        sfx.stream = AudioStream("sounds/jump.wav")
        sfx.play()
    """

    # 信号
    finished = Signal("finished")

    def __init__(self, name: str = "AudioPlayer"):
        super().__init__(name)
        self.stream: Optional[AudioStream] = None
        self.volume_db: float = 0.0
        self.pitch_scale: float = 1.0
        self.autoplay: bool = False
        self.bus: str = "Master"
        self.mix_target: str = "stereo"  # "stereo", "surround", "center"

        self._playing = False
        self._position = 0.0
        self._paused = False

    def play(self, from_position: float = 0.0):
        """播放音频。"""
        self._playing = True
        self._position = from_position
        self._paused = False

    def stop(self):
        """停止播放。"""
        self._playing = False
        self._position = 0.0

    def pause(self):
        """暂停播放。"""
        self._paused = True

    def resume(self):
        """恢复播放。"""
        self._paused = False

    def is_playing(self) -> bool:
        return self._playing and not self._paused

    def get_playback_position(self) -> float:
        return self._position

    def seek(self, position: float):
        self._position = position

    def _ready(self):
        if self.autoplay:
            self.play()


class AudioPlayer2D(Node2D):
    """2D 空间音频播放器 - 参考 Godot AudioStreamPlayer2D。

    音量随与监听者（Camera2D）的距离衰减。

    用法:
        engine_sound = AudioPlayer2D("EngineSound")
        engine_sound.stream = AudioStream("sounds/engine.ogg")
        engine_sound.max_distance = 500
        engine_sound.attenuation = 1.0  # 1/r 衰减
        car.add_child(engine_sound)
        engine_sound.play()
    """

    # 信号
    finished = Signal("finished")

    def __init__(self, name: str = "AudioPlayer2D"):
        super().__init__(name)
        self.stream: Optional[AudioStream] = None
        self.volume_db: float = 0.0
        self.pitch_scale: float = 1.0
        self.autoplay: bool = False
        self.bus: str = "Master"
        self.max_distance: float = 2000.0
        self.attenuation: float = 1.0
        self.area_mask: int = 1
        self.max_polyphony: int = 1

        self._playing = False
        self._position = 0.0

    def play(self, from_position: float = 0.0):
        self._playing = True
        self._position = from_position

    def stop(self):
        self._playing = False
        self._position = 0.0

    def is_playing(self) -> bool:
        return self._playing

    def get_playback_position(self) -> float:
        return self._position

    def _ready(self):
        if self.autoplay:
            self.play()


# === 音频管理器 ===

class AudioManager:
    """全局音频管理器 - 管理音频总线和资源缓存。

    用法:
        AudioManager.load("jump", "sounds/jump.wav")
        AudioManager.play("jump")
        AudioManager.set_bus_volume("SFX", -5)
    """

    _instance = None
    _sounds: Dict[str, AudioStream] = {}
    _buses: Dict[str, AudioBus] = {}
    _music_player: Optional[AudioPlayer] = None

    @classmethod
    def load(cls, name: str, path: str, loop: bool = False):
        """加载音频资源。"""
        stream = AudioStream(path)
        stream.loop = loop
        cls._sounds[name] = stream

    @classmethod
    def play(cls, name: str, volume_db: float = 0.0):
        """播放已加载的音效。"""
        if name in cls._sounds:
            # 创建临时播放器
            player = AudioPlayer(f"_sfx_{name}")
            player.stream = cls._sounds[name]
            player.volume_db = volume_db
            player.play()
            return player
        return None

    @classmethod
    def play_music(cls, name_or_path: str, volume_db: float = 0.0, loop: bool = True):
        """播放背景音乐。"""
        if cls._music_player is None:
            cls._music_player = AudioPlayer("_music")

        stream = cls._sounds.get(name_or_path)
        if stream is None:
            stream = AudioStream(name_or_path)
        stream.loop = loop

        cls._music_player.stream = stream
        cls._music_player.volume_db = volume_db
        cls._music_player.play()

    @classmethod
    def stop_music(cls):
        if cls._music_player:
            cls._music_player.stop()

    @classmethod
    def set_master_volume(cls, volume_db: float):
        bus = cls._buses.setdefault("Master", AudioBus("Master"))
        bus.volume_db = volume_db

    @classmethod
    def set_bus_volume(cls, bus_name: str, volume_db: float):
        bus = cls._buses.setdefault(bus_name, AudioBus(bus_name))
        bus.volume_db = volume_db

    @classmethod
    def mute(cls, bus_name: str = "Master"):
        bus = cls._buses.setdefault(bus_name, AudioBus(bus_name))
        bus.mute = True

    @classmethod
    def unmute(cls, bus_name: str = "Master"):
        bus = cls._buses.setdefault(bus_name, AudioBus(bus_name))
        bus.mute = False
