"""Sprite2D and PhysicsSprite classes for the Scrawl Python API."""

import math
import random
import os
from typing import Optional, Tuple

from .node import Node, Node2D, _scrawl_command_queue, _Node2DVector
from .math_utils import Vector2


_DIRTY_TRANSFORM = 1 << 0
_DIRTY_VISIBLE = 1 << 1
_DIRTY_COLOR = 1 << 2
_DIRTY_COSTUME = 1 << 3
_DIRTY_PEN = 1 << 4
_DIRTY_DIMENSIONS = 1 << 5
_DIRTY_DRAW_ORDER = 1 << 6
_DIRTY_ALL = (1 << 7) - 1

def queue_broadcast(event: str):
    """Queue a broadcast for the runtime."""
    _scrawl_command_queue.append(("broadcast", event))


def queue_text(sprite, text: str, font_size: float = 20.0, color: tuple = (255, 255, 255)):
    """Queue persistent text attached to a sprite."""
    _scrawl_command_queue.append(("text", sprite, text, font_size, color))


def queue_say(sprite, text: str, duration: int = 2000):
    """Queue temporary speech text attached to a sprite."""
    _scrawl_command_queue.append(("say", sprite, text, int(duration)))


def queue_play_sound(path: str, volume: float = None):
    """Queue a one-shot sound effect."""
    if volume is None:
        _scrawl_command_queue.append(("play_sound", path))
    else:
        _scrawl_command_queue.append(("play_sound", path, float(volume)))


def queue_play_music(path: str, loops: int = -1, volume: float = None):
    """Queue background music playback."""
    if volume is None:
        _scrawl_command_queue.append(("play_music", path, int(loops)))
    else:
        _scrawl_command_queue.append(("play_music", path, int(loops), float(volume)))


def queue_stop_music():
    """Queue background music stop."""
    _scrawl_command_queue.append(("stop_music",))


def queue_pause_music():
    """Queue background music pause."""
    _scrawl_command_queue.append(("pause_music",))


def queue_resume_music():
    """Queue background music resume."""
    _scrawl_command_queue.append(("resume_music",))


class Sprite2D(Node2D):
    """A renderable, scriptable 2D node.

    The canonical transform is inherited from :class:`Node2D` using
    ``position``, ``rotation`` and ``scale``. Scratch-style ``x``, ``y``,
    ``direction`` and ``size`` aliases remain available for easy scripting.
    """

    _scrawl_node_kind = "sprite2d"

    def __init__(self, name: str = "Sprite2D"):
        super().__init__(name)
        self._scrawl_dirty = _DIRTY_ALL
        self._width = None
        self._height = None
        self._color = (255, 100, 100)
        self._costumes = {}
        self._current_costume = None
        self._pen_down = False
        self._pen_color = (0, 0, 0)
        self._pen_size = 2
        self.collision_type = "mask"
        self.is_clones = False
        # Match Godot's Node2D defaults.  A scene or parent decides where a
        # node lives; keeping the local origin at (0, 0) makes child sprites
        # attach naturally to physics bodies and containers.
        self.position = Vector2(0.0, 0.0)

    def _mark_node_dirty(self):
        super()._mark_node_dirty()
        if "_scrawl_dirty" in self.__dict__:
            self._scrawl_dirty |= _DIRTY_TRANSFORM

    def _mark_dirty(self, flag: int):
        self._scrawl_dirty |= flag

    def _take_dirty(self) -> int:
        dirty = self._scrawl_dirty
        self._scrawl_dirty = 0
        return dirty

    # ========================================================================
    # Properties
    # ========================================================================

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def x(self) -> float:
        return self._position.x

    @x.setter
    def x(self, value: float):
        self.position = Vector2(value, self._position.y)

    @property
    def y(self) -> float:
        return self._position.y

    @y.setter
    def y(self, value: float):
        self.position = Vector2(self._position.x, value)

    @property
    def direction(self) -> float:
        # Scrawl keeps Scratch-style compass directions as a convenience:
        # 0 points up and 90 points right.  Node2D rotation remains the
        # canonical Godot-style transform where an unrotated sprite is 0.
        return 90.0 - self.rotation_degrees

    @direction.setter
    def direction(self, value: float):
        self.rotation_degrees = 90.0 - float(value)

    @property
    def size(self) -> float:
        return self._scale.x

    @size.setter
    def size(self, value: float):
        self.scale = Vector2(float(value), float(value))

    @property
    def width(self) -> Optional[float]:
        """Custom sprite width in pixels, or ``None`` for the asset width."""
        return self._width

    @width.setter
    def width(self, value: Optional[float]):
        if value is None:
            self._width = None
        else:
            value = float(value)
            if not math.isfinite(value):
                raise ValueError("sprite width must be finite")
            self._width = max(0.0, value)
        self._mark_dirty(_DIRTY_DIMENSIONS)

    @property
    def height(self) -> Optional[float]:
        """Custom sprite height in pixels, or ``None`` for the asset height."""
        return self._height

    @height.setter
    def height(self, value: Optional[float]):
        if value is None:
            self._height = None
        else:
            value = float(value)
            if not math.isfinite(value):
                raise ValueError("sprite height must be finite")
            self._height = max(0.0, value)
        self._mark_dirty(_DIRTY_DIMENSIONS)

    @property
    def z_index(self) -> int:
        return super().z_index

    @z_index.setter
    def z_index(self, value: int):
        self._z_index = int(value)
        self._mark_dirty(_DIRTY_DRAW_ORDER)

    @property
    def color(self) -> Tuple[int, int, int]:
        return self._color

    @color.setter
    def color(self, value):
        if not isinstance(value, (tuple, list)) or len(value) != 3:
            raise TypeError("color must be an (r, g, b) tuple")
        self._color = tuple(max(0, min(255, int(channel))) for channel in value)
        self._mark_dirty(_DIRTY_COLOR)

    @property
    def visible(self) -> bool:
        return super().visible

    @visible.setter
    def visible(self, value: bool):
        self._visible = bool(value)
        self._mark_dirty(_DIRTY_VISIBLE)

    def set_size(self, s: float):
        """Set uniform sprite scale."""
        self.size = s

    def set_dimensions(self, width: Optional[float], height: Optional[float]):
        """Set an explicit render size in pixels."""
        self.width = width
        self.height = height
        self._mark_dirty(_DIRTY_DIMENSIONS)

    def set_collision_type(self, mode: str):
        """Set collision mode: 'rect', 'circle', or 'mask'."""
        if mode in ("rect", "circle", "mask"):
            self.collision_type = mode

    # ========================================================================
    # Movement
    # ========================================================================

    def move(self, steps: float):
        """Move in current direction (compass: 0=up, 90=right, Y-up)."""
        d_rad = math.radians(self.direction)
        self.position = Vector2(
            self._position.x + math.sin(d_rad) * steps,
            self._position.y + math.cos(d_rad) * steps,
        )

    def move_up(self, steps: float):
        self.y += steps

    def move_down(self, steps: float):
        self.y -= steps

    def move_left(self, steps: float):
        self.x -= steps

    def move_right(self, steps: float):
        self.x += steps

    def turn_left(self, degrees: float):
        self.direction -= degrees

    def turn_right(self, degrees: float):
        self.direction += degrees

    def go_to(self, x: float, y: float):
        self.position = Vector2(x, y)

    def point_towards(self, x: float, y: float):
        """Point towards a world position (compass: 0=up, 90=right, Y-up)."""
        dx = x - self.x
        dy = y - self.y
        if dx != 0 or dy != 0:
            self.direction = math.degrees(math.atan2(dx, dy))

    def face_towards(self, target_name: str):
        """Point towards a named sprite in the current scene."""
        if self.scene:
            for s in self.scene.sprites:
                if s.name == target_name:
                    self.point_towards(s.x, s.y)
                    return

    def face_random_direction(self):
        """Point in a random direction."""
        self.direction = random.uniform(0, 360)

    # ========================================================================
    # Appearance
    # ========================================================================

    def add_costume(self, name: str, image_or_path):
        """Add a costume from an image path."""
        if not isinstance(image_or_path, (str, bytes, os.PathLike)):
            raise TypeError("Costumes must be filesystem paths")
        self._costumes[name] = os.fspath(image_or_path)

        if self._current_costume is None:
            self._current_costume = name

    def switch_costume(self, name: str):
        if name in self._costumes:
            self._current_costume = name
            self._mark_dirty(_DIRTY_COSTUME)

    def next_costume(self):
        """Switch to next costume."""
        keys = list(self._costumes.keys())
        if keys and self._current_costume in keys:
            idx = (keys.index(self._current_costume) + 1) % len(keys)
            self._current_costume = keys[idx]
            self._mark_dirty(_DIRTY_COSTUME)

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def say(self, text: str, duration: int = 2000):
        queue_say(self, text, duration)

    def set_text(self, text: str, font_size: float = 20.0, color: tuple = (255, 255, 255)):
        """Display persistent text at this sprite's position.
        Call with empty string to clear."""
        queue_text(self, text, font_size, color)

    # ========================================================================
    # Clone / Delete
    # ========================================================================

    def clone(self, other=None):
        """Clone this sprite, or clone another sprite at this position."""
        target = other if other is not None else self
        new_sprite = object.__new__(type(target))
        new_sprite.__dict__.update(target.__dict__)
        new_sprite._scrawl_node_id = next(Node._scrawl_id_source)
        new_sprite._parent = None
        new_sprite._children = []
        new_sprite._position = _Node2DVector(
            new_sprite, target._position.x, target._position.y
        )
        new_sprite._scale = _Node2DVector(
            new_sprite, target._scale.x, target._scale.y
        )
        new_sprite.is_clones = True
        new_sprite._costumes = dict(target._costumes)
        new_sprite._position = _Node2DVector(
            new_sprite, self._position.x, self._position.y
        )  # Clone spawns at cloner's position
        new_sprite._scrawl_dirty = _DIRTY_ALL
        new_sprite._scrawl_node_dirty = True
        parent = self.get_parent() or self.scene
        if parent:
            parent.add_child(new_sprite)
        return new_sprite

    def delete_self(self):
        """Delete this sprite from the scene."""
        parent = self.get_parent()
        if parent is not None:
            parent.remove_child(self)
        elif self._runtime_bridge_active():
            _scrawl_command_queue.append(("node_remove", self))

    # ========================================================================
    # Events / Broadcast
    # ========================================================================

    def broadcast(self, event: str):
        """Send a broadcast message."""
        queue_broadcast(event)

    def play_sound(self, name: str):
        """Play a sound registered on the game."""
        if self.game is None:
            return
        self.game.play_sound(name)

    # ========================================================================
    # Pen
    # ========================================================================

    def pen_down(self):
        self._pen_down = True
        self._mark_dirty(_DIRTY_PEN)

    def pen_up(self):
        self._pen_down = False
        self._mark_dirty(_DIRTY_PEN)

    def set_pen_color(self, r: int, g: int, b: int):
        self._pen_color = (r, g, b)
        self._mark_dirty(_DIRTY_PEN)

    def set_pen_size(self, size: float):
        self._pen_size = size
        self._mark_dirty(_DIRTY_PEN)


class PhysicsSprite(Sprite2D):
    """A sprite with physics (velocity, gravity, friction, elasticity)."""

    def __init__(self):
        super().__init__()
        self._velocity_x = 0.0
        self._velocity_y = 0.0
        self._gravity = 0.5
        self._friction = 0.02
        self._elasticity = 0.8
        self._angular_velocity = 0.0
        self._velocity_proxy = _PhysicsVelocityProxy(self)

    @property
    def velocity(self):
        """Mutable two-dimensional velocity view."""
        return self._velocity_proxy

    def set_gravity(self, gx: float, gy: float):
        """Set gravity; the vertical component drives this sprite."""
        self._gravity = gy

    def set_elasticity(self, e: float):
        self._elasticity = e

    def set_friction(self, f: float):
        self._friction = f

    @property
    def velocity_x(self):
        return self._velocity_x

    @velocity_x.setter
    def velocity_x(self, v):
        self._velocity_x = float(v)

    @property
    def velocity_y(self):
        return self._velocity_y

    @velocity_y.setter
    def velocity_y(self, v):
        self._velocity_y = float(v)

    @property
    def gravity(self):
        return self._gravity

    @gravity.setter
    def gravity(self, v):
        self._gravity = float(v)

    @property
    def friction(self):
        return self._friction

    @friction.setter
    def friction(self, v):
        self._friction = float(v)

    @property
    def elasticity(self):
        return self._elasticity

    @elasticity.setter
    def elasticity(self, v):
        self._elasticity = float(v)


class _PhysicsVelocityProxy:
    """Mutable view used by ``sprite.velocity.x/y``."""
    def __init__(self, sprite):
        self._s = sprite

    @property
    def x(self):
        return self._s._velocity_x

    @x.setter
    def x(self, v):
        self._s._velocity_x = float(v)

    @property
    def y(self):
        return self._s._velocity_y

    @y.setter
    def y(self, v):
        self._s._velocity_y = float(v)
