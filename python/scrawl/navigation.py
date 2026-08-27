"""
导航/寻路系统 - 参考 Godot Navigation2D / NavigationAgent2D。

提供基于 A* 算法的 2D 寻路功能。

用法:
    # 基于网格的寻路
    nav = NavigationGrid(width=20, height=15, cell_size=32)
    nav.set_cell_solid(5, 3, True)  # 设置障碍

    path = nav.find_path(Vector2(0, 0), Vector2(10, 10))
    for point in path:
        print(point)

    # 导航代理
    agent = NavigationAgent2D()
    agent.target_position = Vector2(500, 400)
    enemy.add_child(agent)
"""

import heapq
import math
from typing import List, Optional, Tuple, Set, Dict
from .node import Node2D
from .math_utils import Vector2
from .signals import Signal


class NavigationGrid:
    """基于网格的 2D 寻路。

    使用 A* 算法在网格上查找路径。
    """

    def __init__(self, width: int = 20, height: int = 15, cell_size: float = 32):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self._solid: Set[Tuple[int, int]] = set()
        self._weights: Dict[Tuple[int, int], float] = {}
        self.diagonal_movement = True

    def set_cell_solid(self, x: int, y: int, solid: bool = True):
        """设置单元格是否为障碍。"""
        if solid:
            self._solid.add((x, y))
        else:
            self._solid.discard((x, y))

    def is_cell_solid(self, x: int, y: int) -> bool:
        return (x, y) in self._solid

    def set_cell_weight(self, x: int, y: int, weight: float):
        """设置单元格的通行代价（越高越难通过）。"""
        self._weights[(x, y)] = weight

    def get_cell_weight(self, x: int, y: int) -> float:
        return self._weights.get((x, y), 1.0)

    def clear(self):
        self._solid.clear()
        self._weights.clear()

    def world_to_grid(self, world_pos: Vector2) -> Tuple[int, int]:
        return (int(world_pos.x / self.cell_size), int(world_pos.y / self.cell_size))

    def grid_to_world(self, gx: int, gy: int) -> Vector2:
        return Vector2(gx * self.cell_size + self.cell_size / 2,
                      gy * self.cell_size + self.cell_size / 2)

    def find_path(self, start: Vector2, end: Vector2) -> List[Vector2]:
        """使用 A* 算法查找路径。

        Args:
            start: 起始世界坐标
            end: 目标世界坐标

        Returns:
            世界坐标路径点列表（空列表表示无路径）
        """
        sx, sy = self.world_to_grid(start)
        ex, ey = self.world_to_grid(end)

        if not self._is_valid(sx, sy) or not self._is_valid(ex, ey):
            return []
        if self.is_cell_solid(ex, ey):
            return []

        # A*
        open_set = [(0, sx, sy)]
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {(sx, sy): 0}
        f_score: Dict[Tuple[int, int], float] = {(sx, sy): self._heuristic(sx, sy, ex, ey)}

        while open_set:
            _, cx, cy = heapq.heappop(open_set)

            if (cx, cy) == (ex, ey):
                # 重建路径
                path = []
                current = (ex, ey)
                while current in came_from:
                    path.append(self.grid_to_world(*current))
                    current = came_from[current]
                path.append(self.grid_to_world(sx, sy))
                path.reverse()
                return path

            for nx, ny in self._neighbors(cx, cy):
                tentative_g = g_score[(cx, cy)] + self._cost(cx, cy, nx, ny)

                if tentative_g < g_score.get((nx, ny), float('inf')):
                    came_from[(nx, ny)] = (cx, cy)
                    g_score[(nx, ny)] = tentative_g
                    f_score[(nx, ny)] = tentative_g + self._heuristic(nx, ny, ex, ey)
                    heapq.heappush(open_set, (f_score[(nx, ny)], nx, ny))

        return []  # 无路径

    def _is_valid(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def _neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        result = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if self._is_valid(nx, ny) and not self.is_cell_solid(nx, ny):
                result.append((nx, ny))

        if self.diagonal_movement:
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx, ny = x + dx, y + dy
                if (self._is_valid(nx, ny) and not self.is_cell_solid(nx, ny)
                        and not self.is_cell_solid(x + dx, y) and not self.is_cell_solid(x, y + dy)):
                    result.append((nx, ny))

        return result

    def _cost(self, x1: int, y1: int, x2: int, y2: int) -> float:
        base = 1.41421 if abs(x1 - x2) + abs(y1 - y2) > 1 else 1.0
        return base * self.get_cell_weight(x2, y2)

    def _heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        if self.diagonal_movement:
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            return max(dx, dy) + 0.41421 * min(dx, dy)
        return abs(x1 - x2) + abs(y1 - y2)


class NavigationAgent2D(Node2D):
    """2D 导航代理 - 参考 Godot NavigationAgent2D。

    附加到移动实体上，自动沿导航路径移动。
    """

    # 信号
    target_reached = Signal("target_reached")
    velocity_computed = Signal("velocity_computed")
    path_changed = Signal("path_changed")

    def __init__(self, name: str = "NavigationAgent2D"):
        super().__init__(name)
        self._target_position = Vector2()
        self._path: List[Vector2] = []
        self._path_index = 0
        self._navigation: Optional[NavigationGrid] = None

        self.max_speed = 200.0
        self.path_desired_distance = 10.0
        self.target_desired_distance = 10.0
        self.avoidance_enabled = False
        self.radius = 10.0

    @property
    def target_position(self) -> Vector2:
        return self._target_position

    @target_position.setter
    def target_position(self, value: Vector2):
        self._target_position = value
        self._update_path()

    def set_navigation(self, nav: NavigationGrid):
        """设置使用的导航网格。"""
        self._navigation = nav

    def is_navigation_finished(self) -> bool:
        return self._path_index >= len(self._path)

    def is_target_reached(self) -> bool:
        if self._parent and isinstance(self._parent, Node2D):
            return self._parent.global_position.distance_to(self._target_position) <= self.target_desired_distance
        return False

    def is_target_reachable(self) -> bool:
        return len(self._path) > 0

    def get_current_navigation_path(self) -> List[Vector2]:
        return list(self._path)

    def get_next_path_position(self) -> Vector2:
        """获取路径上的下一个目标点。"""
        if self._path_index < len(self._path):
            return self._path[self._path_index]
        return self._target_position

    def get_navigation_velocity(self) -> Vector2:
        """获取建议的导航速度。"""
        if not self._parent or not isinstance(self._parent, Node2D):
            return Vector2()

        target = self.get_next_path_position()
        pos = self._parent.global_position
        direction = target - pos
        dist = direction.length()

        if dist <= self.path_desired_distance:
            self._path_index += 1
            if self._path_index >= len(self._path):
                self.target_reached.emit()
                return Vector2()
            target = self.get_next_path_position()
            direction = target - pos
            dist = direction.length()

        if dist > 0:
            velocity = direction.normalized() * min(self.max_speed, dist)
            self.velocity_computed.emit(velocity)
            return velocity

        return Vector2()

    def _update_path(self):
        """重新计算路径。"""
        if self._navigation and self._parent and isinstance(self._parent, Node2D):
            self._path = self._navigation.find_path(
                self._parent.global_position, self._target_position
            )
            self._path_index = 0
            self.path_changed.emit()
