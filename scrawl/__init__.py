from .engine import Game, Sprite, PhysicsSprite, Scene, as_main, as_clones, handle_broadcast, handle_edge_collision, handle_sprite_collision, on_key, Cat, ParticleSystem

import os

# 获取当前包目录的绝对路径
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))