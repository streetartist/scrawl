"""
数学工具 - Vector2, Rect2, Transform2D

参考 Godot 的数学类型，提供 2D 游戏开发常用的数学工具。
"""

import math
from typing import Tuple, Union


class Vector2:
    """2D 向量，参考 Godot Vector2。"""

    ZERO = None  # 延迟初始化
    ONE = None
    UP = None
    DOWN = None
    LEFT = None
    RIGHT = None

    __slots__ = ('x', 'y')

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = float(x)
        self.y = float(y)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self) -> 'Vector2':
        l = self.length()
        if l == 0:
            return Vector2(0, 0)
        return Vector2(self.x / l, self.y / l)

    def dot(self, other: 'Vector2') -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: 'Vector2') -> float:
        return self.x * other.y - self.y * other.x

    def distance_to(self, other: 'Vector2') -> float:
        return (self - other).length()

    def distance_squared_to(self, other: 'Vector2') -> float:
        return (self - other).length_squared()

    def angle(self) -> float:
        """返回与 X 轴正方向的弧度角。"""
        return math.atan2(self.y, self.x)

    def angle_to(self, other: 'Vector2') -> float:
        return math.atan2(self.cross(other), self.dot(other))

    def rotated(self, angle: float) -> 'Vector2':
        """按弧度旋转向量。"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )

    def lerp(self, to: 'Vector2', weight: float) -> 'Vector2':
        """线性插值。"""
        return Vector2(
            self.x + (to.x - self.x) * weight,
            self.y + (to.y - self.y) * weight
        )

    def move_toward(self, to: 'Vector2', delta: float) -> 'Vector2':
        """向目标移动固定距离。"""
        diff = to - self
        dist = diff.length()
        if dist <= delta or dist == 0:
            return Vector2(to.x, to.y)
        return self + diff / dist * delta

    def clamped(self, max_length: float) -> 'Vector2':
        l = self.length()
        if l > max_length and l > 0:
            return self * (max_length / l)
        return Vector2(self.x, self.y)

    def reflect(self, normal: 'Vector2') -> 'Vector2':
        """根据法线反射向量。"""
        return self - normal * 2.0 * self.dot(normal)

    def bounce(self, normal: 'Vector2') -> 'Vector2':
        return -self.reflect(normal)

    def slide(self, normal: 'Vector2') -> 'Vector2':
        return self - normal * self.dot(normal)

    def abs(self) -> 'Vector2':
        return Vector2(abs(self.x), abs(self.y))

    def sign(self) -> 'Vector2':
        return Vector2(
            (1.0 if self.x > 0 else (-1.0 if self.x < 0 else 0.0)),
            (1.0 if self.y > 0 else (-1.0 if self.y < 0 else 0.0))
        )

    def floor(self) -> 'Vector2':
        return Vector2(math.floor(self.x), math.floor(self.y))

    def ceil(self) -> 'Vector2':
        return Vector2(math.ceil(self.x), math.ceil(self.y))

    def round(self) -> 'Vector2':
        return Vector2(round(self.x), round(self.y))

    def snapped(self, step: 'Vector2') -> 'Vector2':
        """吸附到网格。"""
        return Vector2(
            round(self.x / step.x) * step.x if step.x != 0 else self.x,
            round(self.y / step.y) * step.y if step.y != 0 else self.y
        )

    @staticmethod
    def from_angle(angle: float) -> 'Vector2':
        """从弧度角创建单位向量。"""
        return Vector2(math.cos(angle), math.sin(angle))

    # 运算符重载
    def __add__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Vector2(self.x * other, self.y * other)
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return Vector2(self.x * other, self.y * other)
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Vector2(self.x / other, self.y / other)
        if isinstance(other, Vector2):
            return Vector2(self.x / other.x, self.y / other.y)
        return NotImplemented

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __eq__(self, other):
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        return NotImplemented

    def __iter__(self):
        return iter((self.x, self.y))

    def __repr__(self):
        return f"Vector2({self.x}, {self.y})"

    def __bool__(self):
        return self.x != 0.0 or self.y != 0.0


# 延迟初始化常量
Vector2.ZERO = Vector2(0, 0)
Vector2.ONE = Vector2(1, 1)
Vector2.UP = Vector2(0, -1)
Vector2.DOWN = Vector2(0, 1)
Vector2.LEFT = Vector2(-1, 0)
Vector2.RIGHT = Vector2(1, 0)


class Rect2:
    """2D 矩形，参考 Godot Rect2。"""

    __slots__ = ('position', 'size')

    def __init__(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0):
        self.position = Vector2(x, y)
        self.size = Vector2(width, height)

    @property
    def end(self) -> Vector2:
        return self.position + self.size

    @property
    def center(self) -> Vector2:
        return self.position + self.size * 0.5

    def get_area(self) -> float:
        return self.size.x * self.size.y

    def has_point(self, point: Vector2) -> bool:
        return (self.position.x <= point.x <= self.end.x and
                self.position.y <= point.y <= self.end.y)

    def intersects(self, other: 'Rect2') -> bool:
        return not (self.end.x < other.position.x or
                    self.position.x > other.end.x or
                    self.end.y < other.position.y or
                    self.position.y > other.end.y)

    def intersection(self, other: 'Rect2') -> 'Rect2':
        if not self.intersects(other):
            return Rect2()
        x = max(self.position.x, other.position.x)
        y = max(self.position.y, other.position.y)
        x2 = min(self.end.x, other.end.x)
        y2 = min(self.end.y, other.end.y)
        return Rect2(x, y, x2 - x, y2 - y)

    def merge(self, other: 'Rect2') -> 'Rect2':
        x = min(self.position.x, other.position.x)
        y = min(self.position.y, other.position.y)
        x2 = max(self.end.x, other.end.x)
        y2 = max(self.end.y, other.end.y)
        return Rect2(x, y, x2 - x, y2 - y)

    def grow(self, amount: float) -> 'Rect2':
        return Rect2(
            self.position.x - amount,
            self.position.y - amount,
            self.size.x + amount * 2,
            self.size.y + amount * 2
        )

    def expand(self, to: Vector2) -> 'Rect2':
        begin = Vector2(min(self.position.x, to.x), min(self.position.y, to.y))
        end = Vector2(max(self.end.x, to.x), max(self.end.y, to.y))
        return Rect2(begin.x, begin.y, end.x - begin.x, end.y - begin.y)

    def __repr__(self):
        return f"Rect2({self.position.x}, {self.position.y}, {self.size.x}, {self.size.y})"


class Transform2D:
    """2D 变换矩阵，参考 Godot Transform2D。"""

    def __init__(self, rotation: float = 0.0, position: Vector2 = None, scale: Vector2 = None):
        self.rotation = rotation
        self.position = position or Vector2()
        self.scale = scale or Vector2(1, 1)

    def xform(self, point: Vector2) -> Vector2:
        """将点从局部坐标变换到世界坐标。"""
        rotated = point.rotated(self.rotation)
        scaled = Vector2(rotated.x * self.scale.x, rotated.y * self.scale.y)
        return scaled + self.position

    def xform_inv(self, point: Vector2) -> Vector2:
        """将点从世界坐标变换到局部坐标。"""
        local = point - self.position
        local = Vector2(local.x / self.scale.x, local.y / self.scale.y)
        return local.rotated(-self.rotation)

    def __repr__(self):
        return f"Transform2D(rot={self.rotation}, pos={self.position}, scale={self.scale})"


class Color:
    """颜色类，参考 Godot Color。"""

    __slots__ = ('r', 'g', 'b', 'a')

    def __init__(self, r: float = 1.0, g: float = 1.0, b: float = 1.0, a: float = 1.0):
        self.r = max(0.0, min(1.0, float(r)))
        self.g = max(0.0, min(1.0, float(g)))
        self.b = max(0.0, min(1.0, float(b)))
        self.a = max(0.0, min(1.0, float(a)))

    @classmethod
    def from_rgb8(cls, r: int, g: int, b: int, a: int = 255) -> 'Color':
        """从 0-255 整数值创建颜色。"""
        return cls(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

    @classmethod
    def from_hex(cls, hex_str: str) -> 'Color':
        """从十六进制字符串创建颜色 (#RRGGBB 或 #RRGGBBAA)。"""
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 6:
            r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            return cls.from_rgb8(r, g, b)
        elif len(hex_str) == 8:
            r, g, b, a = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), int(hex_str[6:8], 16)
            return cls.from_rgb8(r, g, b, a)
        return cls()

    def to_rgb8(self) -> Tuple[int, int, int]:
        return (int(self.r * 255), int(self.g * 255), int(self.b * 255))

    def to_rgba8(self) -> Tuple[int, int, int, int]:
        return (int(self.r * 255), int(self.g * 255), int(self.b * 255), int(self.a * 255))

    def lerp(self, to: 'Color', weight: float) -> 'Color':
        return Color(
            self.r + (to.r - self.r) * weight,
            self.g + (to.g - self.g) * weight,
            self.b + (to.b - self.b) * weight,
            self.a + (to.a - self.a) * weight
        )

    def darkened(self, amount: float) -> 'Color':
        return Color(self.r * (1 - amount), self.g * (1 - amount), self.b * (1 - amount), self.a)

    def lightened(self, amount: float) -> 'Color':
        return Color(
            self.r + (1 - self.r) * amount,
            self.g + (1 - self.g) * amount,
            self.b + (1 - self.b) * amount,
            self.a
        )

    def __repr__(self):
        return f"Color({self.r:.2f}, {self.g:.2f}, {self.b:.2f}, {self.a:.2f})"

    # 预定义颜色
    WHITE = None
    BLACK = None
    RED = None
    GREEN = None
    BLUE = None
    YELLOW = None
    CYAN = None
    MAGENTA = None
    TRANSPARENT = None
    ORANGE = None
    PURPLE = None
    GRAY = None
    DARK_GRAY = None
    LIGHT_GRAY = None


Color.WHITE = Color(1, 1, 1, 1)
Color.BLACK = Color(0, 0, 0, 1)
Color.RED = Color(1, 0, 0, 1)
Color.GREEN = Color(0, 1, 0, 1)
Color.BLUE = Color(0, 0, 1, 1)
Color.YELLOW = Color(1, 1, 0, 1)
Color.CYAN = Color(0, 1, 1, 1)
Color.MAGENTA = Color(1, 0, 1, 1)
Color.TRANSPARENT = Color(0, 0, 0, 0)
Color.ORANGE = Color(1, 0.647, 0, 1)
Color.PURPLE = Color(0.627, 0.125, 0.941, 1)
Color.GRAY = Color(0.5, 0.5, 0.5, 1)
Color.DARK_GRAY = Color(0.25, 0.25, 0.25, 1)
Color.LIGHT_GRAY = Color(0.75, 0.75, 0.75, 1)
