"""
Camera2D - 2D 摄像机节点，参考 Godot Camera2D。

功能:
- 跟随目标
- 平滑移动
- 缩放
- 视口限制
- 拖拽边距
- 屏幕震动
"""

import math
import random
from typing import Optional
from .node import Node2D
from .math_utils import Vector2
from .signals import Signal


class Camera2D(Node2D):
    """2D 摄像机 - 参考 Godot Camera2D。

    用法:
        camera = Camera2D()
        camera.target = player
        camera.smoothing_enabled = True
        camera.zoom = Vector2(2, 2)
        scene.add_child(camera)
    """

    # 信号
    zoom_changed = Signal("zoom_changed")

    def __init__(self, name: str = "Camera2D"):
        super().__init__(name)

        # 缩放
        self._zoom = Vector2(1, 1)

        # 跟随
        self._target: Optional[Node2D] = None
        self._offset = Vector2()

        # 平滑
        self.smoothing_enabled = False
        self.smoothing_speed = 5.0

        # 限制
        self.limit_left = -10000
        self.limit_right = 10000
        self.limit_top = -10000
        self.limit_bottom = 10000

        # 拖拽边距
        self.drag_horizontal_enabled = False
        self.drag_vertical_enabled = False
        self.drag_left_margin = 0.2
        self.drag_right_margin = 0.2
        self.drag_top_margin = 0.2
        self.drag_bottom_margin = 0.2

        # 震动效果
        self._shake_amount = 0.0
        self._shake_duration = 0.0
        self._shake_timer = 0.0
        self._shake_offset = Vector2()

        # 是否为当前活跃摄像机
        self.current = True

        # 视口大小（引擎设置）
        self._viewport_size = Vector2(800, 600)

    @property
    def zoom(self) -> Vector2:
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        if isinstance(value, (int, float)):
            self._zoom = Vector2(float(value), float(value))
        elif isinstance(value, (tuple, list)):
            self._zoom = Vector2(float(value[0]), float(value[1]))
        else:
            self._zoom = value
        self.zoom_changed.emit()

    @property
    def target(self) -> Optional[Node2D]:
        return self._target

    @target.setter
    def target(self, node: Optional[Node2D]):
        self._target = node

    @property
    def offset(self) -> Vector2:
        return self._offset

    @offset.setter
    def offset(self, value: Vector2):
        if isinstance(value, (tuple, list)):
            self._offset = Vector2(float(value[0]), float(value[1]))
        else:
            self._offset = value

    def shake(self, amount: float = 10.0, duration: float = 0.5):
        """触发屏幕震动效果。

        Args:
            amount: 震动强度（像素）
            duration: 持续时间（秒）
        """
        self._shake_amount = amount
        self._shake_duration = duration
        self._shake_timer = duration

    def get_camera_position(self) -> Vector2:
        """获取摄像机最终位置（含震动偏移）。"""
        base = self.global_position + self._offset
        return base + self._shake_offset

    def get_camera_screen_center(self) -> Vector2:
        """获取摄像机屏幕中心的世界坐标。"""
        return self.get_camera_position()

    def screen_to_world(self, screen_pos: Vector2) -> Vector2:
        """将屏幕坐标转换为世界坐标。"""
        cam_pos = self.get_camera_position()
        half_viewport = self._viewport_size * 0.5
        world_x = cam_pos.x + (screen_pos.x - half_viewport.x) / self._zoom.x
        world_y = cam_pos.y + (screen_pos.y - half_viewport.y) / self._zoom.y
        return Vector2(world_x, world_y)

    def world_to_screen(self, world_pos: Vector2) -> Vector2:
        """将世界坐标转换为屏幕坐标。"""
        cam_pos = self.get_camera_position()
        half_viewport = self._viewport_size * 0.5
        screen_x = (world_pos.x - cam_pos.x) * self._zoom.x + half_viewport.x
        screen_y = (world_pos.y - cam_pos.y) * self._zoom.y + half_viewport.y
        return Vector2(screen_x, screen_y)

    def _process(self, delta: float):
        """每帧更新摄像机。"""
        # 跟随目标
        if self._target and isinstance(self._target, Node2D):
            target_pos = self._target.global_position

            if self.smoothing_enabled:
                current = Vector2(self._position.x, self._position.y)
                self._position = current.lerp(target_pos, self.smoothing_speed * delta)
            else:
                self._position = Vector2(target_pos.x, target_pos.y)

        # 应用限制
        self._apply_limits()

        # 更新震动
        if self._shake_timer > 0:
            self._shake_timer -= delta
            t = self._shake_timer / self._shake_duration if self._shake_duration > 0 else 0
            intensity = self._shake_amount * t
            self._shake_offset = Vector2(
                random.uniform(-intensity, intensity),
                random.uniform(-intensity, intensity)
            )
        else:
            self._shake_offset = Vector2()

    def _apply_limits(self):
        """应用视口边界限制。"""
        half_w = self._viewport_size.x / (2.0 * self._zoom.x)
        half_h = self._viewport_size.y / (2.0 * self._zoom.y)

        self._position.x = max(self.limit_left + half_w,
                               min(self._position.x, self.limit_right - half_w))
        self._position.y = max(self.limit_top + half_h,
                               min(self._position.y, self.limit_bottom - half_h))
