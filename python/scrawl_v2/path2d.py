"""
路径和线条 - 参考 Godot Path2D / Line2D。

用法:
    # 路径（NPC 巡逻路线）
    patrol = Path2D("PatrolPath")
    patrol.add_point(Vector2(100, 100))
    patrol.add_point(Vector2(300, 100))
    patrol.add_point(Vector2(300, 300))
    patrol.add_point(Vector2(100, 300))
    patrol.closed = True

    follower = PathFollow2D("PatrolFollower")
    patrol.add_child(follower)
    follower.speed = 100

    # 线段渲染
    trail = Line2D("Trail")
    trail.width = 3
    trail.default_color = (100, 200, 255, 200)
    trail.add_point(Vector2(0, 0))
    trail.add_point(Vector2(100, 50))
"""

from typing import List
from .node import Node2D
from .math_utils import Vector2
from .signals import Signal


class Path2D(Node2D):
    """2D 路径 - 参考 Godot Path2D。

    定义一条 2D 路径，可以被 PathFollow2D 跟随。
    """

    def __init__(self, name: str = "Path2D"):
        super().__init__(name)
        self.points: List[Vector2] = []
        self.closed = False

    def add_point(self, point: Vector2, index: int = -1):
        if index < 0:
            self.points.append(point)
        else:
            self.points.insert(index, point)

    def remove_point(self, index: int):
        if 0 <= index < len(self.points):
            self.points.pop(index)

    def set_point(self, index: int, point: Vector2):
        if 0 <= index < len(self.points):
            self.points[index] = point

    def get_point(self, index: int) -> Vector2:
        if 0 <= index < len(self.points):
            return self.points[index]
        return Vector2()

    def get_point_count(self) -> int:
        return len(self.points)

    def get_total_length(self) -> float:
        """获取路径总长度。"""
        total = 0.0
        for i in range(len(self.points) - 1):
            total += self.points[i].distance_to(self.points[i + 1])
        if self.closed and len(self.points) > 1:
            total += self.points[-1].distance_to(self.points[0])
        return total

    def get_point_at_offset(self, offset: float) -> Vector2:
        """获取路径上指定偏移量处的点。"""
        if not self.points:
            return Vector2()
        if len(self.points) == 1:
            return self.points[0]

        segments = list(self._segments())
        remaining = offset
        for start, end in segments:
            seg_len = start.distance_to(end)
            if remaining <= seg_len:
                t = remaining / seg_len if seg_len > 0 else 0
                return start.lerp(end, t)
            remaining -= seg_len
        return self.points[-1] if not self.closed else self.points[0]

    def _segments(self):
        for i in range(len(self.points) - 1):
            yield self.points[i], self.points[i + 1]
        if self.closed and len(self.points) > 1:
            yield self.points[-1], self.points[0]


class PathFollow2D(Node2D):
    """路径跟随者 - 参考 Godot PathFollow2D。

    沿 Path2D 父节点定义的路径移动。
    """

    def __init__(self, name: str = "PathFollow2D"):
        super().__init__(name)
        self.progress = 0.0
        self.progress_ratio = 0.0  # 0~1
        self.speed = 100.0
        self.rotates = True
        self.loop = True
        self._moving = True

    def _process(self, delta: float):
        if not self._moving or not self._parent:
            return

        path = self._parent
        if not isinstance(path, Path2D) or not path.points:
            return

        total_len = path.get_total_length()
        if total_len == 0:
            return

        self.progress += self.speed * delta

        if self.loop:
            self.progress = self.progress % total_len
        else:
            if self.progress >= total_len:
                self.progress = total_len
                self._moving = False

        self.progress_ratio = self.progress / total_len
        self._position = path.get_point_at_offset(self.progress)


class Line2D(Node2D):
    """2D 线段 - 参考 Godot Line2D。"""

    def __init__(self, name: str = "Line2D"):
        super().__init__(name)
        self.points: List[Vector2] = []
        self.width = 2.0
        self.default_color = (255, 255, 255, 255)
        self.joint_mode = 0  # 0=none, 1=sharp, 2=round
        self.begin_cap_mode = 0
        self.end_cap_mode = 0
        self.antialiased = False
        self.closed = False

    def add_point(self, point: Vector2, index: int = -1):
        if index < 0:
            self.points.append(point)
        else:
            self.points.insert(index, point)

    def remove_point(self, index: int):
        if 0 <= index < len(self.points):
            self.points.pop(index)

    def set_point(self, index: int, point: Vector2):
        if 0 <= index < len(self.points):
            self.points[index] = point

    def get_point_count(self) -> int:
        return len(self.points)

    def clear_points(self):
        self.points.clear()
