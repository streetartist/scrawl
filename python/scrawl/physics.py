"""
物理系统 - 参考 Godot 的 2D 物理节点。

提供:
- CollisionShape2D: 碰撞形状
- RigidBody2D: 刚体（受物理引擎控制）
- StaticBody2D: 静态体（不移动的碰撞体）
- KinematicBody2D: 运动学体（代码控制移动，带碰撞检测）
- Area2D: 区域检测（触发器）
- RayCast2D: 射线检测
"""

import math
from typing import List, Optional, Tuple, Callable, Dict
from .node import Node2D
from .math_utils import Vector2, Rect2
from .signals import Signal


# === 碰撞形状 ===

class CollisionShape2D(Node2D):
    """碰撞形状节点 - 参考 Godot CollisionShape2D。"""

    def __init__(self, name: str = "CollisionShape2D"):
        super().__init__(name)
        self.shape: Optional['Shape2D'] = None
        self.disabled = False
        self.one_way_collision = False
        self.debug_color = (0, 150, 255, 100)

    def set_rect(self, width: float, height: float):
        """设置矩形碰撞。"""
        self.shape = RectangleShape2D(width, height)

    def set_circle(self, radius: float):
        """设置圆形碰撞。"""
        self.shape = CircleShape2D(radius)

    def set_capsule(self, radius: float, height: float):
        """设置胶囊碰撞。"""
        self.shape = CapsuleShape2D(radius, height)

    def set_polygon(self, points: List[Vector2]):
        """设置多边形碰撞。"""
        self.shape = ConvexPolygonShape2D(points)


class Shape2D:
    """碰撞形状基类。"""

    def get_rect(self) -> Rect2:
        return Rect2()


class RectangleShape2D(Shape2D):
    """矩形碰撞形状。"""

    def __init__(self, width: float = 32, height: float = 32):
        self.size = Vector2(width, height)

    def get_rect(self) -> Rect2:
        hw, hh = self.size.x / 2, self.size.y / 2
        return Rect2(-hw, -hh, self.size.x, self.size.y)


class CircleShape2D(Shape2D):
    """圆形碰撞形状。"""

    def __init__(self, radius: float = 16):
        self.radius = radius

    def get_rect(self) -> Rect2:
        return Rect2(-self.radius, -self.radius, self.radius * 2, self.radius * 2)


class CapsuleShape2D(Shape2D):
    """胶囊碰撞形状。"""

    def __init__(self, radius: float = 16, height: float = 32):
        self.radius = radius
        self.height = height


class ConvexPolygonShape2D(Shape2D):
    """凸多边形碰撞形状。"""

    def __init__(self, points: List[Vector2] = None):
        self.points = points or []


class SegmentShape2D(Shape2D):
    """线段碰撞形状。"""

    def __init__(self, a: Vector2 = None, b: Vector2 = None):
        self.a = a or Vector2()
        self.b = b or Vector2()


# === 碰撞检测结果 ===

class KinematicCollision2D:
    """运动学碰撞结果 - 参考 Godot KinematicCollision2D。"""

    def __init__(self):
        self.position = Vector2()
        self.normal = Vector2()
        self.collider: Optional[Node2D] = None
        self.collider_velocity = Vector2()
        self.remainder = Vector2()
        self.travel = Vector2()


# === 物理体 ===

class PhysicsBody2D(Node2D):
    """物理体基类。"""

    def __init__(self, name: str = ""):
        super().__init__(name)
        self.collision_layer: int = 1
        self.collision_mask: int = 1
        self._colliders: List[CollisionShape2D] = []

    def set_collision_layer_value(self, layer: int, value: bool):
        if value:
            self.collision_layer |= (1 << (layer - 1))
        else:
            self.collision_layer &= ~(1 << (layer - 1))

    def set_collision_mask_value(self, layer: int, value: bool):
        if value:
            self.collision_mask |= (1 << (layer - 1))
        else:
            self.collision_mask &= ~(1 << (layer - 1))

    def get_collision_shapes(self) -> List[CollisionShape2D]:
        """获取所有碰撞形状子节点。"""
        return [c for c in self._children if isinstance(c, CollisionShape2D)]

    def get_bounding_rect(self) -> Rect2:
        """获取碰撞体的包围盒。"""
        shapes = self.get_collision_shapes()
        if not shapes:
            return Rect2(self._position.x - 16, self._position.y - 16, 32, 32)

        rect = None
        for shape in shapes:
            if shape.shape:
                sr = shape.shape.get_rect()
                sr_world = Rect2(
                    sr.position.x + self._position.x + shape._position.x,
                    sr.position.y + self._position.y + shape._position.y,
                    sr.size.x, sr.size.y
                )
                if rect is None:
                    rect = sr_world
                else:
                    rect = rect.merge(sr_world)
        return rect or Rect2(self._position.x - 16, self._position.y - 16, 32, 32)


class StaticBody2D(PhysicsBody2D):
    """静态体 - 参考 Godot StaticBody2D。

    不移动的碰撞体，用于地面、墙壁等。

    用法:
        ground = StaticBody2D("Ground")
        shape = CollisionShape2D()
        shape.set_rect(800, 32)
        ground.add_child(shape)
        ground.position = Vector2(400, 580)
    """

    def __init__(self, name: str = "StaticBody2D"):
        super().__init__(name)
        self.constant_linear_velocity = Vector2()
        self.constant_angular_velocity = 0.0


class RigidBody2D(PhysicsBody2D):
    """刚体 - 参考 Godot RigidBody2D。

    受物理引擎完全控制的物体，支持重力、弹力、摩擦。

    用法:
        ball = RigidBody2D("Ball")
        ball.gravity_scale = 1.0
        ball.bounce = 0.8
        ball.mass = 1.0
    """

    # 信号
    body_entered = Signal("body_entered")
    body_exited = Signal("body_exited")

    # 模式
    MODE_DYNAMIC = 0
    MODE_STATIC = 1
    MODE_KINEMATIC = 2

    def __init__(self, name: str = "RigidBody2D"):
        super().__init__(name)
        self.mode = self.MODE_DYNAMIC
        self.mass = 1.0
        self.gravity_scale = 1.0
        self.linear_velocity = Vector2()
        self.angular_velocity = 0.0
        self.linear_damp = 0.0
        self.angular_damp = 0.0
        self.bounce = 0.0
        self.friction = 1.0
        self.sleeping = False
        self.can_sleep = True
        self.freeze = False

        # 内部物理
        self._force = Vector2()
        self._impulse = Vector2()
        self._torque = 0.0

    def apply_force(self, force: Vector2):
        """施加持续力（每帧累积）。"""
        self._force = self._force + force

    def apply_impulse(self, impulse: Vector2):
        """施加瞬时冲量。"""
        self._impulse = self._impulse + impulse

    def apply_torque(self, torque: float):
        """施加扭矩。"""
        self._torque += torque

    def apply_central_impulse(self, impulse: Vector2):
        """施加中心冲量。"""
        self.linear_velocity = self.linear_velocity + impulse / self.mass

    def _physics_process(self, delta: float):
        """物理帧更新。"""
        if self.freeze or self.sleeping or self.mode != self.MODE_DYNAMIC:
            return

        # 重力
        gravity = Vector2(0, 980.0 * self.gravity_scale)

        # 加速度 = 力 / 质量 + 重力
        acceleration = self._force / self.mass + gravity

        # 更新速度
        self.linear_velocity = self.linear_velocity + (acceleration * delta) + self._impulse / self.mass
        self.angular_velocity += self._torque / self.mass * delta

        # 阻尼
        self.linear_velocity = self.linear_velocity * (1.0 - self.linear_damp * delta)
        self.angular_velocity *= (1.0 - self.angular_damp * delta)

        # 更新位置
        self._position = self._position + self.linear_velocity * delta
        self._rotation += self.angular_velocity * delta

        # 清除力
        self._force = Vector2()
        self._impulse = Vector2()
        self._torque = 0.0


class KinematicBody2D(PhysicsBody2D):
    """运动学体 - 参考 Godot CharacterBody2D (Godot 4)。

    代码控制移动，自带碰撞检测和滑动。

    用法:
        class Player(KinematicBody2D):
            def __init__(self):
                super().__init__("Player")
                self.speed = 200
                self.velocity = Vector2()

            def _physics_process(self, delta):
                # 获取输入
                direction = Vector2()
                if Input.is_action_pressed("move_right"):
                    direction.x += 1
                if Input.is_action_pressed("move_left"):
                    direction.x -= 1
                self.velocity = direction * self.speed
                self.move_and_slide()
    """

    # 信号
    body_entered = Signal("body_entered")

    def __init__(self, name: str = "KinematicBody2D"):
        super().__init__(name)
        self.velocity = Vector2()
        self.up_direction = Vector2(0, -1)
        self.floor_max_angle = math.radians(45)
        self.max_slides = 4
        self.floor_snap_length = 1.0

        self._on_floor = False
        self._on_wall = False
        self._on_ceiling = False
        self._last_collision: Optional[KinematicCollision2D] = None

    def move_and_slide(self) -> Vector2:
        """按照 velocity 移动，并在碰到碰撞体时滑动。

        Returns:
            剩余速度
        """
        # 简化实现：直接移动位置
        self._position = self._position + self.velocity * (1.0 / 60.0)
        return self.velocity

    def move_and_collide(self, motion: Vector2) -> Optional[KinematicCollision2D]:
        """按照给定运动向量移动，碰到第一个碰撞体时停止。"""
        self._position = self._position + motion
        return self._last_collision

    def is_on_floor(self) -> bool:
        return self._on_floor

    def is_on_wall(self) -> bool:
        return self._on_wall

    def is_on_ceiling(self) -> bool:
        return self._on_ceiling

    def get_floor_normal(self) -> Vector2:
        if self._last_collision:
            return self._last_collision.normal
        return Vector2(0, -1)

    def get_slide_collision(self, index: int = 0) -> Optional[KinematicCollision2D]:
        return self._last_collision


class Area2D(Node2D):
    """区域检测 - 参考 Godot Area2D。

    用于检测物体进入/退出区域，不产生物理碰撞。

    用法:
        coin = Area2D("Coin")
        shape = CollisionShape2D()
        shape.set_circle(16)
        coin.add_child(shape)
        coin.body_entered.connect(on_coin_collected)
    """

    # 信号
    body_entered = Signal("body_entered")
    body_exited = Signal("body_exited")
    area_entered = Signal("area_entered")
    area_exited = Signal("area_exited")

    def __init__(self, name: str = "Area2D"):
        super().__init__(name)
        self.monitoring = True
        self.monitorable = True
        self.collision_layer = 1
        self.collision_mask = 1
        self.gravity = 0.0
        self.gravity_direction = Vector2(0, 1)
        self.gravity_point = False
        self.gravity_point_center = Vector2()
        self.linear_damp = 0.0
        self.angular_damp = 0.0

        self._overlapping_bodies: List[PhysicsBody2D] = []
        self._overlapping_areas: List['Area2D'] = []

    def get_overlapping_bodies(self) -> List[PhysicsBody2D]:
        return list(self._overlapping_bodies)

    def get_overlapping_areas(self) -> List['Area2D']:
        return list(self._overlapping_areas)

    def has_overlapping_bodies(self) -> bool:
        return len(self._overlapping_bodies) > 0

    def has_overlapping_areas(self) -> bool:
        return len(self._overlapping_areas) > 0


class RayCast2D(Node2D):
    """射线检测 - 参考 Godot RayCast2D。

    从起点沿方向发射射线，检测碰到的第一个碰撞体。

    用法:
        ray = RayCast2D()
        ray.target_position = Vector2(0, 100)
        ray.enabled = True
        if ray.is_colliding():
            hit_point = ray.get_collision_point()
    """

    def __init__(self, name: str = "RayCast2D"):
        super().__init__(name)
        self.enabled = True
        self.target_position = Vector2(0, 50)
        self.collision_mask = 1
        self.collide_with_areas = False
        self.collide_with_bodies = True
        self.hit_from_inside = False

        self._is_colliding = False
        self._collision_point = Vector2()
        self._collision_normal = Vector2()
        self._collider: Optional[Node2D] = None

    def is_colliding(self) -> bool:
        return self._is_colliding

    def get_collision_point(self) -> Vector2:
        return self._collision_point

    def get_collision_normal(self) -> Vector2:
        return self._collision_normal

    def get_collider(self) -> Optional[Node2D]:
        return self._collider

    def force_raycast_update(self):
        """强制立即更新射线检测结果。"""
        # 简化实现：由引擎主循环调用
        pass
