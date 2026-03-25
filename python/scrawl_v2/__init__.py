"""
Scrawl v2 - A simple yet powerful 2D game engine.

Built on Bevy (Rust) for performance, with a Scratch-like Python API.

Basic usage:
    from scrawl_v2 import *

    game = Game(width=800, height=600, title="My Game")

    class Ball(Sprite):
        def __init__(self):
            super().__init__()
            self.name = "Ball"

        @as_main
        def main_loop(self):
            while True:
                self.turn_left(10)
                self.move(10)
                yield 100

    class MyScene(Scene):
        def __init__(self):
            super().__init__()
            self.add_sprite(Ball())

    game.set_scene(MyScene())
    game.run()
"""

__version__ = "2.0.0-alpha.1"

from .engine import Game
from .scene import Scene
from .sprite import Sprite, PhysicsSprite
from .events import (
    as_main,
    as_clones,
    on_key,
    on_mouse,
    on_broadcast,
    on_sprite_clicked,
    on_edge_collision,
    on_sprite_collision,
)
from .constants import *

__all__ = [
    "Game",
    "Scene",
    "Sprite",
    "PhysicsSprite",
    "as_main",
    "as_clones",
    "on_key",
    "on_mouse",
    "on_broadcast",
    "on_sprite_clicked",
    "on_edge_collision",
    "on_sprite_collision",
]
