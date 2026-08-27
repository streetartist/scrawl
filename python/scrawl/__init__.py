"""Scrawl's public Python API, powered by the Rust/Bevy runtime.

``Game``, ``Scene``, ``Sprite`` and their event decorators are the stable
native-runtime surface. Other exported node models are experimental until
their bridge mappings are listed as connected in ``docs/MANUAL.md``.
"""

__version__ = "2.2.0"

# === 核心 ===
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

# === 数学工具 ===
from .math_utils import Vector2, Rect2, Transform2D, Color

# === 节点系统 ===
from .node import Node, Node2D
from .signals import Signal, SignalInstance

# === 物理 ===
from .physics import (
    CollisionShape2D,
    RectangleShape2D, CircleShape2D, CapsuleShape2D, ConvexPolygonShape2D, SegmentShape2D,
    PhysicsBody2D, StaticBody2D, RigidBody2D, KinematicBody2D,
    Area2D, RayCast2D,
    KinematicCollision2D,
)

# === 动画 ===
from .animation import (
    SpriteFrames, AnimatedSprite2D,
    Animation, AnimationTrack, AnimationPlayer,
    Tween,
)

# === 摄像机 ===
from .camera import Camera2D

# === 音频 ===
from .audio import (
    AudioStream, AudioBus,
    AudioPlayer, AudioPlayer2D,
    AudioManager,
)

# === 瓦片地图 ===
from .tilemap import TileData, TileSet, TileMap, TileMapLayer

# === 粒子 ===
from .particles import ParticleEmitter2D

# === UI ===
from .ui import (
    CanvasLayer, Control,
    Label, Button, TextureButton,
    ProgressBar, TextEdit, LineEdit,
    Panel, ColorRect, TextureRect, NinePatchRect,
    HBoxContainer, VBoxContainer, GridContainer,
)

# === 输入 ===
from .input_map import (
    Input, InputMap,
    InputEvent, InputEventKey, InputEventMouseButton, InputEventMouseMotion,
    InputEventJoypadButton, InputEventJoypadMotion,
)

# === 计时器 ===
from .timer import Timer

# === 导航 ===
from .navigation import NavigationGrid, NavigationAgent2D

# === 光照 ===
from .light2d import Light2D, PointLight2D, DirectionalLight2D, LightOccluder2D, CanvasModulate

# === 路径 ===
from .path2d import Path2D, PathFollow2D, Line2D

# === 状态机 ===
from .state_machine import State, StateMachine

# === 资源 ===
from .resources import Resource, ImageTexture, AudioResource, FontResource, ResourceLoader

__all__ = [
    # 核心
    "Game", "Scene", "Sprite", "PhysicsSprite",
    # 事件装饰器
    "as_main", "as_clones", "on_key", "on_mouse",
    "on_broadcast", "on_sprite_clicked", "on_edge_collision", "on_sprite_collision",
    # 数学
    "Vector2", "Rect2", "Transform2D", "Color",
    # 节点
    "Node", "Node2D",
    # 信号
    "Signal", "SignalInstance",
    # 物理
    "CollisionShape2D",
    "RectangleShape2D", "CircleShape2D", "CapsuleShape2D", "ConvexPolygonShape2D", "SegmentShape2D",
    "PhysicsBody2D", "StaticBody2D", "RigidBody2D", "KinematicBody2D",
    "Area2D", "RayCast2D", "KinematicCollision2D",
    # 动画
    "SpriteFrames", "AnimatedSprite2D",
    "Animation", "AnimationTrack", "AnimationPlayer",
    "Tween",
    # 摄像机
    "Camera2D",
    # 音频
    "AudioStream", "AudioBus", "AudioPlayer", "AudioPlayer2D", "AudioManager",
    # 瓦片地图
    "TileData", "TileSet", "TileMap", "TileMapLayer",
    # 粒子
    "ParticleEmitter2D",
    # UI
    "CanvasLayer", "Control",
    "Label", "Button", "TextureButton",
    "ProgressBar", "TextEdit", "LineEdit",
    "Panel", "ColorRect", "TextureRect", "NinePatchRect",
    "HBoxContainer", "VBoxContainer", "GridContainer",
    # 输入
    "Input", "InputMap",
    "InputEvent", "InputEventKey", "InputEventMouseButton", "InputEventMouseMotion",
    "InputEventJoypadButton", "InputEventJoypadMotion",
    # 计时器
    "Timer",
    # 导航
    "NavigationGrid", "NavigationAgent2D",
    # 光照
    "Light2D", "PointLight2D", "DirectionalLight2D", "LightOccluder2D", "CanvasModulate",
    # 路径
    "Path2D", "PathFollow2D", "Line2D",
    # 状态机
    "State", "StateMachine",
    # 资源
    "Resource", "ImageTexture", "AudioResource", "FontResource", "ResourceLoader",
]
