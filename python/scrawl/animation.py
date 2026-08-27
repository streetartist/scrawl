"""
动画系统 - 参考 Godot 的动画节点。

提供:
- AnimatedSprite2D: 精灵表动画
- AnimationPlayer: 通用属性动画
- Tween: 补间动画（一次性动画效果）
"""

from typing import Dict, List, Optional, Callable, Any, Tuple
from .node import Node, Node2D
from .math_utils import Vector2
from .signals import Signal


# === 精灵表动画 ===

class SpriteFrames:
    """精灵帧集合 - 参考 Godot SpriteFrames。

    管理多组动画帧。

    用法:
        frames = SpriteFrames()
        frames.add_animation("idle")
        frames.add_frame("idle", "sprites/idle_0.png")
        frames.add_frame("idle", "sprites/idle_1.png")
        frames.set_animation_speed("idle", 8)
    """

    def __init__(self):
        self._animations: Dict[str, _AnimationData] = {}
        self.add_animation("default")

    def add_animation(self, name: str):
        if name not in self._animations:
            self._animations[name] = _AnimationData(name)

    def remove_animation(self, name: str):
        if name != "default":
            self._animations.pop(name, None)

    def has_animation(self, name: str) -> bool:
        return name in self._animations

    def get_animation_names(self) -> List[str]:
        return list(self._animations.keys())

    def add_frame(self, animation: str, frame, index: int = -1):
        """添加帧（可以是图片路径或其他资源）。"""
        if animation in self._animations:
            anim = self._animations[animation]
            if index < 0:
                anim.frames.append(frame)
            else:
                anim.frames.insert(index, frame)

    def remove_frame(self, animation: str, index: int):
        if animation in self._animations:
            anim = self._animations[animation]
            if 0 <= index < len(anim.frames):
                anim.frames.pop(index)

    def get_frame_count(self, animation: str) -> int:
        if animation in self._animations:
            return len(self._animations[animation].frames)
        return 0

    def get_frame(self, animation: str, index: int):
        if animation in self._animations:
            anim = self._animations[animation]
            if 0 <= index < len(anim.frames):
                return anim.frames[index]
        return None

    def set_animation_speed(self, animation: str, fps: float):
        if animation in self._animations:
            self._animations[animation].speed = fps

    def get_animation_speed(self, animation: str) -> float:
        if animation in self._animations:
            return self._animations[animation].speed
        return 5.0

    def set_animation_loop(self, animation: str, loop: bool):
        if animation in self._animations:
            self._animations[animation].loop = loop


class _AnimationData:
    def __init__(self, name: str):
        self.name = name
        self.frames: List = []
        self.speed: float = 5.0  # FPS
        self.loop: bool = True


class AnimatedSprite2D(Node2D):
    """动画精灵 - 参考 Godot AnimatedSprite2D。

    用法:
        sprite = AnimatedSprite2D()
        sprite.sprite_frames = my_frames
        sprite.play("run")
    """

    # 信号
    animation_finished = Signal("animation_finished")
    frame_changed = Signal("frame_changed")
    animation_changed = Signal("animation_changed")

    def __init__(self, name: str = "AnimatedSprite2D"):
        super().__init__(name)
        self.sprite_frames: Optional[SpriteFrames] = None
        self._current_animation = "default"
        self._frame = 0
        self._playing = False
        self._speed_scale = 1.0
        self._timer = 0.0
        self.flip_h = False
        self.flip_v = False
        self.centered = True

    @property
    def animation(self) -> str:
        return self._current_animation

    @property
    def frame(self) -> int:
        return self._frame

    @frame.setter
    def frame(self, value: int):
        if self._frame != value:
            self._frame = value
            self.frame_changed.emit()

    @property
    def speed_scale(self) -> float:
        return self._speed_scale

    @speed_scale.setter
    def speed_scale(self, value: float):
        self._speed_scale = value

    def play(self, animation: str = "", from_frame: int = 0):
        """播放动画。"""
        if animation:
            if self._current_animation != animation:
                self._current_animation = animation
                self.animation_changed.emit()
            self._frame = from_frame
        self._playing = True
        self._timer = 0.0

    def stop(self):
        """停止动画。"""
        self._playing = False

    def is_playing(self) -> bool:
        return self._playing

    def get_frame_texture(self):
        """获取当前帧的纹理/路径。"""
        if self.sprite_frames:
            return self.sprite_frames.get_frame(self._current_animation, self._frame)
        return None

    def _process(self, delta: float):
        if not self._playing or not self.sprite_frames:
            return

        anim = self.sprite_frames._animations.get(self._current_animation)
        if not anim or not anim.frames:
            return

        fps = anim.speed * self._speed_scale
        if fps <= 0:
            return

        self._timer += delta
        frame_duration = 1.0 / fps

        while self._timer >= frame_duration:
            self._timer -= frame_duration
            next_frame = self._frame + 1

            if next_frame >= len(anim.frames):
                if anim.loop:
                    self._frame = 0
                else:
                    self._playing = False
                    self.animation_finished.emit()
                    return
            else:
                self._frame = next_frame
            self.frame_changed.emit()


# === 属性动画 ===

class AnimationTrack:
    """动画轨道 - 对象某属性的关键帧序列。"""

    def __init__(self, target_path: str, property_name: str):
        self.target_path = target_path
        self.property_name = property_name
        self.keyframes: List[Tuple[float, Any]] = []  # (time, value)
        self.interpolation = "linear"  # linear, cubic, nearest

    def add_keyframe(self, time: float, value: Any):
        self.keyframes.append((time, value))
        self.keyframes.sort(key=lambda k: k[0])

    def get_value_at(self, time: float) -> Any:
        if not self.keyframes:
            return None
        if time <= self.keyframes[0][0]:
            return self.keyframes[0][1]
        if time >= self.keyframes[-1][0]:
            return self.keyframes[-1][1]

        # 找到前后关键帧
        for i in range(len(self.keyframes) - 1):
            t0, v0 = self.keyframes[i]
            t1, v1 = self.keyframes[i + 1]
            if t0 <= time <= t1:
                weight = (time - t0) / (t1 - t0) if t1 != t0 else 0
                return self._interpolate(v0, v1, weight)
        return self.keyframes[-1][1]

    def _interpolate(self, a, b, t):
        if self.interpolation == "nearest":
            return a if t < 0.5 else b
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a + (b - a) * t
        if isinstance(a, Vector2) and isinstance(b, Vector2):
            return a.lerp(b, t)
        if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(min(len(a), len(b))))
        return b


class Animation:
    """动画资源 - 参考 Godot Animation。"""

    def __init__(self, name: str = ""):
        self.name = name
        self.length: float = 1.0
        self.loop = False
        self.tracks: List[AnimationTrack] = []

    def add_track(self, target_path: str, property_name: str) -> AnimationTrack:
        track = AnimationTrack(target_path, property_name)
        self.tracks.append(track)
        return track


class AnimationPlayer(Node):
    """动画播放器 - 参考 Godot AnimationPlayer。

    播放基于关键帧的属性动画。

    用法:
        anim_player = AnimationPlayer()
        anim = Animation("bounce")
        anim.length = 1.0
        track = anim.add_track(".", "position")
        track.add_keyframe(0.0, Vector2(0, 0))
        track.add_keyframe(0.5, Vector2(0, -50))
        track.add_keyframe(1.0, Vector2(0, 0))
        anim_player.add_animation("bounce", anim)
        anim_player.play("bounce")
    """

    # 信号
    animation_finished = Signal("animation_finished")
    animation_started = Signal("animation_started")
    animation_changed = Signal("animation_changed")

    def __init__(self, name: str = "AnimationPlayer"):
        super().__init__(name)
        self._animations: Dict[str, Animation] = {}
        self._current_animation = ""
        self._playing = False
        self._time = 0.0
        self._speed_scale = 1.0
        self._autoplay = ""

    def add_animation(self, name: str, animation: Animation):
        self._animations[name] = animation

    def remove_animation(self, name: str):
        self._animations.pop(name, None)

    def has_animation(self, name: str) -> bool:
        return name in self._animations

    def get_animation_list(self) -> List[str]:
        return list(self._animations.keys())

    def play(self, animation: str = "", from_time: float = 0.0):
        if animation:
            if animation in self._animations:
                if self._current_animation != animation:
                    self._current_animation = animation
                    self.animation_changed.emit()
                self._time = from_time
                self._playing = True
                self.animation_started.emit()

    def stop(self):
        self._playing = False

    def is_playing(self) -> bool:
        return self._playing

    @property
    def current_animation(self) -> str:
        return self._current_animation

    @property
    def current_animation_position(self) -> float:
        return self._time

    def seek(self, time: float):
        self._time = time

    def _process(self, delta: float):
        if not self._playing or not self._current_animation:
            return

        anim = self._animations.get(self._current_animation)
        if not anim:
            return

        self._time += delta * self._speed_scale

        # 应用所有轨道
        for track in anim.tracks:
            self._apply_track(track, self._time)

        # 检查是否完成
        if self._time >= anim.length:
            if anim.loop:
                self._time = self._time % anim.length
            else:
                self._playing = False
                self.animation_finished.emit()

    def _apply_track(self, track: AnimationTrack, time: float):
        """将轨道的值应用到目标节点。"""
        node = self._parent
        if not node:
            return

        if track.target_path != ".":
            node = node.get_node(track.target_path)

        if node is None:
            return

        value = track.get_value_at(time)
        if value is not None and hasattr(node, track.property_name):
            setattr(node, track.property_name, value)


# === 补间动画 ===

class Tween:
    """补间动画 - 参考 Godot Tween。

    一次性的属性动画，适合简单的过渡效果。

    用法:
        tween = Tween()
        tween.tween_property(sprite, "position", Vector2(100, 200), 0.5)
        tween.tween_property(sprite, "modulate", (255, 255, 255, 0), 0.3).set_delay(0.5)
        tween.play()

    缓动函数:
        "linear", "ease_in", "ease_out", "ease_in_out",
        "back_in", "back_out", "bounce_out", "elastic_out"
    """

    # 信号
    finished = Signal("finished")
    step_finished = Signal("step_finished")

    def __init__(self):
        self._tweeners: List['_Tweener'] = []
        self._running = False
        self._time = 0.0
        self._loops = 1  # 0 = 无限循环
        self._current_loop = 0
        self._parallel = False
        self._speed_scale = 1.0

    def tween_property(self, target, property_name: str, final_value, duration: float) -> '_PropertyTweener':
        """创建属性补间。"""
        tweener = _PropertyTweener(target, property_name, final_value, duration)
        self._tweeners.append(tweener)
        return tweener

    def tween_callback(self, callback: Callable) -> '_CallbackTweener':
        """创建回调补间（在特定时间点调用函数）。"""
        tweener = _CallbackTweener(callback)
        self._tweeners.append(tweener)
        return tweener

    def tween_interval(self, duration: float) -> '_IntervalTweener':
        """创建等待补间。"""
        tweener = _IntervalTweener(duration)
        self._tweeners.append(tweener)
        return tweener

    def tween_method(self, method: Callable, from_value, to_value, duration: float) -> '_MethodTweener':
        """创建方法补间（每帧调用方法并传入插值后的值）。"""
        tweener = _MethodTweener(method, from_value, to_value, duration)
        self._tweeners.append(tweener)
        return tweener

    def set_loops(self, loops: int = 0) -> 'Tween':
        self._loops = loops
        return self

    def set_parallel(self, parallel: bool = True) -> 'Tween':
        self._parallel = parallel
        return self

    def set_speed_scale(self, speed: float) -> 'Tween':
        self._speed_scale = speed
        return self

    def play(self):
        """开始播放补间。"""
        self._running = True
        self._time = 0.0
        for t in self._tweeners:
            t._started = False
            t._finished = False

    def stop(self):
        self._running = False

    def kill(self):
        self._running = False
        self._tweeners.clear()

    def is_running(self) -> bool:
        return self._running

    def update(self, delta: float):
        """更新补间（由引擎调用）。"""
        if not self._running:
            return

        self._time += delta * self._speed_scale

        if self._parallel:
            all_done = True
            for tweener in self._tweeners:
                if not tweener._finished:
                    tweener.update(delta)
                    if not tweener._finished:
                        all_done = False
            if all_done:
                self._on_loop_done()
        else:
            # 顺序执行
            for tweener in self._tweeners:
                if not tweener._finished:
                    if not tweener._started:
                        tweener._start()
                    tweener.update(delta)
                    if not tweener._finished:
                        break
            else:
                self._on_loop_done()

    def _on_loop_done(self):
        self._current_loop += 1
        if self._loops == 0 or self._current_loop < self._loops:
            # 重新开始
            self._time = 0.0
            for t in self._tweeners:
                t._started = False
                t._finished = False
        else:
            self._running = False
            self.finished.emit()


class _Tweener:
    """补间器基类。"""

    def __init__(self):
        self._delay = 0.0
        self._delay_timer = 0.0
        self._started = False
        self._finished = False

    def set_delay(self, delay: float) -> '_Tweener':
        self._delay = delay
        return self

    def _start(self):
        self._started = True
        self._delay_timer = self._delay

    def update(self, delta: float):
        if self._delay_timer > 0:
            self._delay_timer -= delta
            return


class _PropertyTweener(_Tweener):
    """属性补间器。"""

    def __init__(self, target, property_name: str, final_value, duration: float):
        super().__init__()
        self.target = target
        self.property_name = property_name
        self.final_value = final_value
        self.duration = duration
        self._initial_value = None
        self._elapsed = 0.0
        self._ease_type = "linear"
        self._trans_type = "linear"

    def set_ease(self, ease_type: str) -> '_PropertyTweener':
        self._ease_type = ease_type
        return self

    def set_trans(self, trans_type: str) -> '_PropertyTweener':
        self._trans_type = trans_type
        return self

    def from_value(self, value) -> '_PropertyTweener':
        self._initial_value = value
        return self

    def _start(self):
        super()._start()
        if self._initial_value is None:
            self._initial_value = getattr(self.target, self.property_name)
        self._elapsed = 0.0

    def update(self, delta: float):
        super().update(delta)
        if self._delay_timer > 0:
            return

        if not self._started:
            self._start()

        self._elapsed += delta
        t = min(self._elapsed / self.duration, 1.0) if self.duration > 0 else 1.0
        t = _apply_ease(t, self._ease_type)

        value = _interpolate_value(self._initial_value, self.final_value, t)
        setattr(self.target, self.property_name, value)

        if self._elapsed >= self.duration:
            self._finished = True


class _CallbackTweener(_Tweener):
    def __init__(self, callback: Callable):
        super().__init__()
        self.callback = callback

    def update(self, delta: float):
        super().update(delta)
        if self._delay_timer > 0:
            return
        self.callback()
        self._finished = True


class _IntervalTweener(_Tweener):
    def __init__(self, duration: float):
        super().__init__()
        self.duration = duration
        self._elapsed = 0.0

    def _start(self):
        super()._start()
        self._elapsed = 0.0

    def update(self, delta: float):
        super().update(delta)
        if self._delay_timer > 0:
            return
        if not self._started:
            self._start()
        self._elapsed += delta
        if self._elapsed >= self.duration:
            self._finished = True


class _MethodTweener(_Tweener):
    def __init__(self, method: Callable, from_value, to_value, duration: float):
        super().__init__()
        self.method = method
        self.from_value = from_value
        self.to_value = to_value
        self.duration = duration
        self._elapsed = 0.0
        self._ease_type = "linear"

    def set_ease(self, ease_type: str) -> '_MethodTweener':
        self._ease_type = ease_type
        return self

    def _start(self):
        super()._start()
        self._elapsed = 0.0

    def update(self, delta: float):
        super().update(delta)
        if self._delay_timer > 0:
            return
        if not self._started:
            self._start()
        self._elapsed += delta
        t = min(self._elapsed / self.duration, 1.0) if self.duration > 0 else 1.0
        t = _apply_ease(t, self._ease_type)
        value = _interpolate_value(self.from_value, self.to_value, t)
        self.method(value)
        if self._elapsed >= self.duration:
            self._finished = True


# === 缓动函数 ===

def _apply_ease(t: float, ease_type: str) -> float:
    """应用缓动函数。"""
    import math

    if ease_type == "linear":
        return t
    elif ease_type == "ease_in":
        return t * t
    elif ease_type == "ease_out":
        return 1 - (1 - t) * (1 - t)
    elif ease_type == "ease_in_out":
        if t < 0.5:
            return 2 * t * t
        return 1 - (-2 * t + 2) ** 2 / 2
    elif ease_type == "back_in":
        c1 = 1.70158
        return (c1 + 1) * t * t * t - c1 * t * t
    elif ease_type == "back_out":
        c1 = 1.70158
        return 1 + (c1 + 1) * ((t - 1) ** 3) + c1 * ((t - 1) ** 2)
    elif ease_type == "bounce_out":
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    elif ease_type == "elastic_out":
        if t == 0 or t == 1:
            return t
        return 2 ** (-10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1
    return t


def _interpolate_value(a, b, t: float):
    """在两个值之间插值。"""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * t
    if isinstance(a, Vector2) and isinstance(b, Vector2):
        return a.lerp(b, t)
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(min(len(a), len(b))))
    return b if t >= 1 else a
