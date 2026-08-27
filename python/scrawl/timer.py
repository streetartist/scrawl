"""
计时器 - 参考 Godot Timer。

用法:
    timer = Timer("SpawnTimer")
    timer.wait_time = 2.0
    timer.autostart = True
    timer.one_shot = False
    timer.timeout.connect(spawn_enemy)
    scene.add_child(timer)
"""

from .node import Node
from .signals import Signal


class Timer(Node):
    """计时器节点 - 参考 Godot Timer。

    在设定的时间间隔后发射 timeout 信号。
    """

    # 信号
    timeout = Signal("timeout")

    # 处理模式
    TIMER_PROCESS_PHYSICS = 0
    TIMER_PROCESS_IDLE = 1

    def __init__(self, name: str = "Timer"):
        super().__init__(name)
        self.wait_time = 1.0
        self.one_shot = False
        self.autostart = False
        self.paused = False
        self.process_callback = self.TIMER_PROCESS_IDLE

        self._time_left = 0.0
        self._running = False

    @property
    def time_left(self) -> float:
        return self._time_left

    def start(self, time_sec: float = -1.0):
        """启动计时器。"""
        if time_sec > 0:
            self.wait_time = time_sec
        self._time_left = self.wait_time
        self._running = True

    def stop(self):
        """停止计时器。"""
        self._running = False
        self._time_left = 0.0

    def is_stopped(self) -> bool:
        return not self._running

    def _ready(self):
        if self.autostart:
            self.start()

    def _process(self, delta: float):
        if not self._running or self.paused:
            return
        if self.process_callback != self.TIMER_PROCESS_IDLE:
            return

        self._tick(delta)

    def _physics_process(self, delta: float):
        if not self._running or self.paused:
            return
        if self.process_callback != self.TIMER_PROCESS_PHYSICS:
            return

        self._tick(delta)

    def _tick(self, delta: float):
        self._time_left -= delta
        if self._time_left <= 0:
            self.timeout.emit()
            if self.one_shot:
                self._running = False
                self._time_left = 0.0
            else:
                self._time_left = self.wait_time + self._time_left  # 保留剩余时间
