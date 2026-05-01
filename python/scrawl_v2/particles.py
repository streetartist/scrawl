"""
粒子系统 - 参考 Godot CPUParticles2D。

提供 2D 粒子效果，如火焰、烟雾、爆炸、雨雪等。

用法:
    # 火焰效果
    fire = ParticleEmitter2D("Fire")
    fire.amount = 50
    fire.lifetime = 1.0
    fire.direction = Vector2(0, -1)
    fire.spread = 30
    fire.gravity = Vector2(0, -50)
    fire.initial_velocity_min = 50
    fire.initial_velocity_max = 100
    fire.color_start = Color.from_rgb8(255, 200, 50)
    fire.color_end = Color.from_rgb8(255, 50, 0, 0)
    fire.emitting = True

    # 爆炸效果
    explosion = ParticleEmitter2D.create_preset("explosion")
"""

import math
import random
from typing import List, Optional, Tuple
from .node import Node2D
from .math_utils import Vector2, Color
from .signals import Signal


class _Particle:
    """内部粒子状态。"""

    __slots__ = ('position', 'velocity', 'acceleration', 'rotation', 'angular_velocity',
                 'scale', 'color', 'lifetime', 'age', 'alive')

    def __init__(self):
        self.position = Vector2()
        self.velocity = Vector2()
        self.acceleration = Vector2()
        self.rotation = 0.0
        self.angular_velocity = 0.0
        self.scale = 1.0
        self.color = (255, 255, 255, 255)
        self.lifetime = 1.0
        self.age = 0.0
        self.alive = False


class ParticleEmitter2D(Node2D):
    """2D 粒子发射器 - 参考 Godot CPUParticles2D。"""

    # 信号
    finished = Signal("finished")

    # 发射形状
    EMISSION_SHAPE_POINT = 0
    EMISSION_SHAPE_SPHERE = 1
    EMISSION_SHAPE_RECT = 2

    def __init__(self, name: str = "ParticleEmitter2D"):
        super().__init__(name)

        # 基本属性
        self.emitting = False
        self.amount = 16
        self.lifetime = 1.0
        self.one_shot = False
        self.preprocess = 0.0
        self.speed_scale = 1.0
        self.explosiveness = 0.0  # 0=均匀发射, 1=同时发射所有
        self.randomness = 0.0

        # 发射形状
        self.emission_shape = self.EMISSION_SHAPE_POINT
        self.emission_sphere_radius = 1.0
        self.emission_rect_extents = Vector2(1, 1)

        # 方向
        self.direction = Vector2(0, -1)
        self.spread = 45.0  # 角度

        # 重力
        self.gravity = Vector2(0, 98)

        # 初速度
        self.initial_velocity_min = 0.0
        self.initial_velocity_max = 50.0

        # 角速度
        self.angular_velocity_min = 0.0
        self.angular_velocity_max = 0.0

        # 缩放
        self.scale_min = 1.0
        self.scale_max = 1.0
        self.scale_curve_min = 1.0  # 生命周期结束时的缩放
        self.scale_curve_max = 0.0

        # 颜色
        self.color_start = Color.from_rgb8(255, 255, 255, 255)
        self.color_end = Color.from_rgb8(255, 255, 255, 0)

        # 阻尼
        self.damping_min = 0.0
        self.damping_max = 0.0

        # 线性加速度
        self.linear_accel_min = 0.0
        self.linear_accel_max = 0.0

        # 内部
        self._particles: List[_Particle] = []
        self._emit_timer = 0.0
        self._active = False

    def restart(self):
        """重新开始发射。"""
        self._particles.clear()
        self._emit_timer = 0.0
        self.emitting = True

    def _process(self, delta: float):
        if not self.emitting and not self._particles:
            return

        dt = delta * self.speed_scale

        # 发射新粒子
        if self.emitting:
            self._emit_timer += dt
            emit_interval = self.lifetime / max(self.amount, 1)
            while self._emit_timer >= emit_interval and len(self._particles) < self.amount:
                self._spawn_particle()
                self._emit_timer -= emit_interval

        # 更新粒子
        alive_particles = []
        for p in self._particles:
            if not p.alive:
                continue

            p.age += dt
            if p.age >= p.lifetime:
                p.alive = False
                continue

            t = p.age / p.lifetime  # 0..1 生命周期进度

            # 物理
            p.velocity = p.velocity + (self.gravity + p.acceleration) * dt

            # 阻尼
            damping = random.uniform(self.damping_min, self.damping_max)
            if damping > 0:
                p.velocity = p.velocity * max(0, 1 - damping * dt)

            p.position = p.position + p.velocity * dt
            p.rotation += p.angular_velocity * dt

            # 缩放随生命周期变化
            start_scale = p.scale
            end_scale = start_scale * random.uniform(self.scale_curve_min, self.scale_curve_max)
            p.scale = start_scale + (end_scale - start_scale) * t

            # 颜色插值
            p.color = self.color_start.lerp(self.color_end, t).to_rgba8()

            alive_particles.append(p)

        self._particles = alive_particles

        # one_shot 检查
        if self.one_shot and self.emitting and not self._particles:
            self.emitting = False
            self.finished.emit()

    def _spawn_particle(self):
        """创建一个新粒子。"""
        p = _Particle()
        p.alive = True
        p.lifetime = self.lifetime * (1 + random.uniform(-self.randomness, self.randomness) * 0.5)
        p.age = 0.0

        # 发射位置
        if self.emission_shape == self.EMISSION_SHAPE_POINT:
            p.position = Vector2()
        elif self.emission_shape == self.EMISSION_SHAPE_SPHERE:
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, self.emission_sphere_radius)
            p.position = Vector2(math.cos(angle) * r, math.sin(angle) * r)
        elif self.emission_shape == self.EMISSION_SHAPE_RECT:
            p.position = Vector2(
                random.uniform(-self.emission_rect_extents.x, self.emission_rect_extents.x),
                random.uniform(-self.emission_rect_extents.y, self.emission_rect_extents.y)
            )

        # 发射方向
        base_angle = math.atan2(self.direction.y, self.direction.x)
        spread_rad = math.radians(self.spread)
        angle = base_angle + random.uniform(-spread_rad, spread_rad)

        speed = random.uniform(self.initial_velocity_min, self.initial_velocity_max)
        p.velocity = Vector2(math.cos(angle) * speed, math.sin(angle) * speed)

        # 角速度
        p.angular_velocity = random.uniform(self.angular_velocity_min, self.angular_velocity_max)

        # 缩放
        p.scale = random.uniform(self.scale_min, self.scale_max)

        # 颜色
        p.color = self.color_start.to_rgba8()

        # 线性加速度
        accel = random.uniform(self.linear_accel_min, self.linear_accel_max)
        p.acceleration = self.direction * accel

        self._particles.append(p)

    def get_particles(self) -> List[_Particle]:
        """获取活跃粒子列表（用于渲染）。"""
        return [p for p in self._particles if p.alive]

    # === 预设 ===

    @classmethod
    def create_preset(cls, preset: str, name: str = "") -> 'ParticleEmitter2D':
        """创建预设粒子效果。

        预设: "fire", "smoke", "explosion", "rain", "snow", "sparkle", "trail"
        """
        emitter = cls(name or preset)

        if preset == "fire":
            emitter.amount = 50
            emitter.lifetime = 0.8
            emitter.direction = Vector2(0, -1)
            emitter.spread = 20
            emitter.gravity = Vector2(0, -30)
            emitter.initial_velocity_min = 40
            emitter.initial_velocity_max = 80
            emitter.color_start = Color.from_rgb8(255, 200, 50, 255)
            emitter.color_end = Color.from_rgb8(255, 50, 0, 0)
            emitter.scale_min = 0.5
            emitter.scale_max = 1.5
            emitter.scale_curve_min = 0.0
            emitter.scale_curve_max = 0.2

        elif preset == "smoke":
            emitter.amount = 30
            emitter.lifetime = 2.0
            emitter.direction = Vector2(0, -1)
            emitter.spread = 15
            emitter.gravity = Vector2(0, -20)
            emitter.initial_velocity_min = 10
            emitter.initial_velocity_max = 30
            emitter.color_start = Color.from_rgb8(150, 150, 150, 200)
            emitter.color_end = Color.from_rgb8(200, 200, 200, 0)
            emitter.scale_min = 1.0
            emitter.scale_max = 2.0
            emitter.damping_min = 0.5
            emitter.damping_max = 1.0

        elif preset == "explosion":
            emitter.amount = 100
            emitter.lifetime = 0.5
            emitter.one_shot = True
            emitter.explosiveness = 1.0
            emitter.direction = Vector2(0, 0)
            emitter.spread = 180
            emitter.gravity = Vector2(0, 50)
            emitter.initial_velocity_min = 100
            emitter.initial_velocity_max = 300
            emitter.color_start = Color.from_rgb8(255, 255, 100, 255)
            emitter.color_end = Color.from_rgb8(255, 50, 0, 0)
            emitter.scale_min = 0.5
            emitter.scale_max = 2.0

        elif preset == "rain":
            emitter.amount = 200
            emitter.lifetime = 1.5
            emitter.direction = Vector2(0.1, 1)
            emitter.spread = 5
            emitter.gravity = Vector2(0, 200)
            emitter.initial_velocity_min = 200
            emitter.initial_velocity_max = 300
            emitter.emission_shape = cls.EMISSION_SHAPE_RECT
            emitter.emission_rect_extents = Vector2(400, 10)
            emitter.color_start = Color.from_rgb8(100, 150, 255, 200)
            emitter.color_end = Color.from_rgb8(100, 150, 255, 100)
            emitter.scale_min = 0.3
            emitter.scale_max = 0.5

        elif preset == "snow":
            emitter.amount = 100
            emitter.lifetime = 5.0
            emitter.direction = Vector2(0, 1)
            emitter.spread = 30
            emitter.gravity = Vector2(0, 15)
            emitter.initial_velocity_min = 10
            emitter.initial_velocity_max = 30
            emitter.emission_shape = cls.EMISSION_SHAPE_RECT
            emitter.emission_rect_extents = Vector2(400, 10)
            emitter.color_start = Color.from_rgb8(255, 255, 255, 255)
            emitter.color_end = Color.from_rgb8(255, 255, 255, 100)
            emitter.angular_velocity_min = -1
            emitter.angular_velocity_max = 1

        elif preset == "sparkle":
            emitter.amount = 20
            emitter.lifetime = 0.5
            emitter.direction = Vector2(0, -1)
            emitter.spread = 180
            emitter.gravity = Vector2(0, 0)
            emitter.initial_velocity_min = 20
            emitter.initial_velocity_max = 60
            emitter.color_start = Color.from_rgb8(255, 255, 100, 255)
            emitter.color_end = Color.from_rgb8(255, 255, 200, 0)
            emitter.scale_min = 0.3
            emitter.scale_max = 1.0

        elif preset == "trail":
            emitter.amount = 30
            emitter.lifetime = 0.3
            emitter.direction = Vector2(0, 0)
            emitter.spread = 5
            emitter.gravity = Vector2(0, 0)
            emitter.initial_velocity_min = 0
            emitter.initial_velocity_max = 5
            emitter.color_start = Color.from_rgb8(100, 200, 255, 200)
            emitter.color_end = Color.from_rgb8(100, 200, 255, 0)
            emitter.damping_min = 2.0
            emitter.damping_max = 3.0

        return emitter
