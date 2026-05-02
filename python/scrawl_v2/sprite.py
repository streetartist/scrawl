"""
Sprite and PhysicsSprite classes - the core game objects.
API compatible with scrawl v1.
"""

import math
import random
import copy

try:
    from scrawl_v2.scrawl_native import NativeSprite, NativePhysicsSprite
    _HAS_NATIVE = True
except ImportError:
    try:
        from scrawl_native import NativeSprite, NativePhysicsSprite
        _HAS_NATIVE = True
    except ImportError:
        _HAS_NATIVE = False

# Global command queue: Rust drains this each frame via _scrawl_command_queue
# Commands: ("clone", sprite_instance), ("delete", sprite_instance), ("broadcast", event_name)
_scrawl_command_queue = []


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


class _Vec2Proxy:
    """Mimics pygame.Vector2 for v1 compat: sprite.pos.x / sprite.pos.y"""
    def __init__(self, sprite):
        self._sprite = sprite

    @property
    def x(self):
        return self._sprite._x

    @x.setter
    def x(self, v):
        self._sprite.x = float(v)

    @property
    def y(self):
        return self._sprite._y

    @y.setter
    def y(self, v):
        self._sprite.y = float(v)

    def __iter__(self):
        return iter((self._sprite._x, self._sprite._y))

    def __repr__(self):
        return f"Vec2({self._sprite._x}, {self._sprite._y})"


class Sprite:
    """A game sprite. API compatible with scrawl v1."""

    def __init__(self):
        self._name = "Sprite"
        self._x = 400.0
        self._y = 300.0
        self._direction = 90.0
        self._size = 1.0
        self._visible = True
        self.color = (255, 100, 100)
        self._costumes = {}
        self._current_costume = None
        self._pen_down = False
        self._pen_color = (0, 0, 0)
        self._pen_size = 2
        self.collision_type = "mask"
        self.scene = None
        self.game = None
        self.is_clones = False

        # v1 compat: pos proxy
        self._pos_proxy = _Vec2Proxy(self)

    # ========================================================================
    # Properties
    # ========================================================================

    @property
    def pos(self):
        """v1 compat: self.pos.x / self.pos.y"""
        return self._pos_proxy

    @pos.setter
    def pos(self, value):
        """Accept tuple, list, or Vector2-like"""
        if hasattr(value, 'x') and hasattr(value, 'y'):
            self._x = float(value.x)
            self._y = float(value.y)
        elif isinstance(value, (tuple, list)) and len(value) >= 2:
            self._x = float(value[0])
            self._y = float(value[1])

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float):
        self._x = float(value)

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float):
        self._y = float(value)

    @property
    def direction(self) -> float:
        return self._direction

    @direction.setter
    def direction(self, value: float):
        self._direction = float(value)

    @property
    def size(self) -> float:
        return self._size

    @size.setter
    def size(self, value: float):
        self._size = float(value)

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        self._visible = value

    def set_size(self, s: float):
        """v1 compat: set sprite scale."""
        self.size = s

    def set_collision_type(self, mode: str):
        """Set collision mode: 'rect', 'circle', or 'mask'."""
        if mode in ("rect", "circle", "mask"):
            self.collision_type = mode

    # ========================================================================
    # Movement
    # ========================================================================

    def move(self, steps: float):
        """Move in current direction (compass: 0=up, 90=right, Y-up)."""
        d_rad = math.radians(self._direction)
        self._x += math.sin(d_rad) * steps
        self._y += math.cos(d_rad) * steps

    def move_up(self, steps: float):
        self._y += steps

    def move_down(self, steps: float):
        self._y -= steps

    def move_left(self, steps: float):
        self._x -= steps

    def move_right(self, steps: float):
        self._x += steps

    def turn_left(self, degrees: float):
        self._direction -= degrees

    def turn_right(self, degrees: float):
        self._direction += degrees

    def go_to(self, x: float, y: float):
        self._x = float(x)
        self._y = float(y)

    def point_towards(self, x: float, y: float):
        """Point towards a world position (compass: 0=up, 90=right, Y-up)."""
        dx = x - self._x
        dy = y - self._y
        if dx != 0 or dy != 0:
            self._direction = math.degrees(math.atan2(dx, dy))

    def face_towards(self, target_name: str):
        """Point towards a named sprite (v1 compat)."""
        if self.scene:
            for s in self.scene._sprites:
                if s.name == target_name:
                    self.point_towards(s.x, s.y)
                    return

    def face_random_direction(self):
        """Point in a random direction (v1 compat)."""
        self._direction = random.uniform(0, 360)

    # ========================================================================
    # Appearance
    # ========================================================================

    def add_costume(self, name: str, image_or_path):
        """Add a costume. Accepts file path (str) or pygame Surface (v1 compat)."""
        if isinstance(image_or_path, str):
            self._costumes[name] = image_or_path
        else:
            # pygame Surface — store as marker, engine will need to handle
            self._costumes[name] = image_or_path

        if self._current_costume is None:
            self._current_costume = name

    def switch_costume(self, name: str):
        if name in self._costumes:
            self._current_costume = name

    def next_costume(self):
        """Switch to next costume."""
        keys = list(self._costumes.keys())
        if keys and self._current_costume in keys:
            idx = (keys.index(self._current_costume) + 1) % len(keys)
            self._current_costume = keys[idx]

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False

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
        """Clone this sprite (or another sprite if given). v1 compat."""
        target = other if other is not None else self
        new_sprite = object.__new__(type(target))
        new_sprite.__dict__.update(target.__dict__)
        new_sprite._pos_proxy = _Vec2Proxy(new_sprite)
        new_sprite.is_clones = True
        new_sprite._costumes = dict(target._costumes)
        new_sprite._x = self._x  # Clone spawns at cloner's position
        new_sprite._y = self._y
        new_sprite._direction = target._direction
        new_sprite._visible = target._visible
        new_sprite.scene = self.scene  # Inherit scene reference
        if self.scene:
            self.scene._sprites.append(new_sprite)
        _scrawl_command_queue.append(("clone", new_sprite))
        return new_sprite

    def delete_self(self):
        """Delete this sprite from the scene. v1 compat."""
        _scrawl_command_queue.append(("delete", self))

    # ========================================================================
    # Events / Broadcast
    # ========================================================================

    def broadcast(self, event: str):
        """Send a broadcast message. v1 compat."""
        queue_broadcast(event)

    def play_sound(self, name: str):
        """Play a named sound. v1 compat."""
        if self.game is None:
            return
        self.game.play_sound(name)

    # ========================================================================
    # Pen
    # ========================================================================

    def pen_down(self):
        self._pen_down = True

    def pen_up(self):
        self._pen_down = False

    def set_pen_color(self, r: int, g: int, b: int):
        self._pen_color = (r, g, b)

    def set_pen_size(self, size: float):
        self._pen_size = size


class PhysicsSprite(Sprite):
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
        """v1 compat: self.velocity.x / self.velocity.y"""
        return self._velocity_proxy

    def set_gravity(self, gx: float, gy: float):
        """v1 compat."""
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
    """v1 compat: sprite.velocity.x / sprite.velocity.y"""
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
