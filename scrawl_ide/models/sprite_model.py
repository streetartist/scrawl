"""
Sprite / Node Data Model

Represents a node (sprite, physics body, camera, light, etc.) in the Scrawl IDE.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid


# ============================================================
# Node type categories and metadata
# ============================================================

NODE_CATEGORIES = {
    "2D节点": ["Sprite", "PhysicsSprite", "AnimatedSprite2D"],
    "物理": ["StaticBody2D", "RigidBody2D", "KinematicBody2D", "Area2D"],
    "摄像机": ["Camera2D"],
    "渲染": ["PointLight2D", "DirectionalLight2D", "Line2D"],
    "音频": ["AudioPlayer2D"],
    "粒子": ["ParticleEmitter2D"],
    "路径": ["Path2D", "PathFollow2D"],
    "地图": ["TileMap"],
    "UI": ["Label", "Button", "ProgressBar", "Panel"],
    "其他": ["Timer", "NavigationAgent2D"],
}

NODE_ICONS = {
    "Sprite": "🎮",
    "PhysicsSprite": "⚡",
    "AnimatedSprite2D": "🎞️",
    "StaticBody2D": "🧱",
    "RigidBody2D": "🎱",
    "KinematicBody2D": "🏃",
    "Area2D": "📦",
    "Camera2D": "📷",
    "PointLight2D": "💡",
    "DirectionalLight2D": "☀️",
    "AudioPlayer2D": "🔊",
    "ParticleEmitter2D": "✨",
    "Path2D": "🛤️",
    "PathFollow2D": "📍",
    "Line2D": "📏",
    "TileMap": "🗺️",
    "Label": "🏷️",
    "Button": "🔘",
    "ProgressBar": "📊",
    "Panel": "🖼️",
    "Timer": "⏱️",
    "NavigationAgent2D": "🧭",
}

# Which node types support costumes/images
VISUAL_NODE_TYPES = {"Sprite", "PhysicsSprite", "AnimatedSprite2D",
                     "StaticBody2D", "RigidBody2D", "KinematicBody2D", "Area2D"}

# Which node types are physics bodies
PHYSICS_NODE_TYPES = {"PhysicsSprite", "StaticBody2D", "RigidBody2D", "KinematicBody2D", "Area2D"}


def _default_node_code(class_name: str, node_type: str = "Sprite") -> str:
    """Generate default code for a node based on its type."""
    templates = {
        "Sprite": f'''class {class_name}(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"

    @as_main
    def main_loop(self):
        """主循环"""
        while True:
            # 在这里添加逻辑
            yield 0
''',
        "PhysicsSprite": f'''class {class_name}(PhysicsSprite):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"

    @as_main
    def main_loop(self):
        """主循环"""
        while True:
            yield 0
''',
        "AnimatedSprite2D": f'''class {class_name}(AnimatedSprite2D):
    def __init__(self):
        frames = SpriteFrames()
        frames.add_animation("default")
        super().__init__(frames)
        self.name = "{class_name}"

    @as_main
    def main_loop(self):
        """主循环"""
        self.play("default")
        while True:
            yield 0
''',
        "StaticBody2D": f'''class {class_name}(StaticBody2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
''',
        "RigidBody2D": f'''class {class_name}(RigidBody2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"

    @as_main
    def main_loop(self):
        """主循环"""
        while True:
            yield 0
''',
        "KinematicBody2D": f'''class {class_name}(KinematicBody2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        self.speed = 200.0

    @as_main
    def main_loop(self):
        """主循环"""
        while True:
            velocity = Input.get_vector("move_left", "move_right", "move_up", "move_down")
            self.move_and_slide(Vector2(velocity.x * self.speed, velocity.y * self.speed))
            yield 0
''',
        "Area2D": f'''class {class_name}(Area2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"

    @as_main
    def main_loop(self):
        """主循环"""
        while True:
            yield 0
''',
        "Camera2D": f'''class {class_name}(Camera2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        self.smoothing_enabled = True
        self.smoothing_speed = 5.0
''',
        "PointLight2D": f'''class {class_name}(PointLight2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        self.energy = 1.0
        self.radius = 200.0
''',
        "DirectionalLight2D": f'''class {class_name}(DirectionalLight2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        self.energy = 0.5
''',
        "AudioPlayer2D": f'''class {class_name}(AudioPlayer2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        # self.stream = AudioStream.load("sounds/effect.ogg")
        self.autoplay = False
''',
        "ParticleEmitter2D": f'''class {class_name}(ParticleEmitter2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        self.amount = 50
        self.lifetime = 2.0
        self.emitting = True
''',
        "Path2D": f'''class {class_name}(Path2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        # 添加路径点
        # self.add_point(Vector2(0, 0))
        # self.add_point(Vector2(100, 0))
''',
        "PathFollow2D": f'''class {class_name}(PathFollow2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        self.speed = 100.0
        self.loop = True
''',
        "Line2D": f'''class {class_name}(Line2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        self.default_color = (255, 255, 255)
        self.width = 2.0
''',
        "TileMap": f'''class {class_name}(TileMap):
    def __init__(self):
        tileset = TileSet(tile_size=32)
        super().__init__(tileset)
        self.name = "{class_name}"
''',
        "Label": f'''class {class_name}(Label):
    def __init__(self):
        super().__init__("Hello")
        self.name = "{class_name}"
        self.font_size = 24
''',
        "Button": f'''class {class_name}(Button):
    def __init__(self):
        super().__init__("Button")
        self.name = "{class_name}"
        self.pressed.connect(self.on_pressed)

    def on_pressed(self):
        pass
''',
        "ProgressBar": f'''class {class_name}(ProgressBar):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        self.min_value = 0
        self.max_value = 100
        self.value = 100
''',
        "Panel": f'''class {class_name}(Panel):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
''',
        "Timer": f'''class {class_name}(Timer):
    def __init__(self):
        super().__init__(wait_time=1.0, one_shot=False)
        self.name = "{class_name}"
        self.timeout.connect(self.on_timeout)

    def on_timeout(self):
        pass
''',
        "NavigationAgent2D": f'''class {class_name}(NavigationAgent2D):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"
        self.max_speed = 200.0
''',
    }
    return templates.get(node_type, templates["Sprite"])


@dataclass
class CostumeData:
    """Data for a single costume."""
    name: str
    path: str = ""  # Image file path (empty for code-drawn costumes)
    draw_code: str = ""  # Drawing code for code-drawn costumes
    width: int = 32  # Width for code-drawn costumes
    height: int = 32  # Height for code-drawn costumes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "draw_code": self.draw_code,
            "width": self.width,
            "height": self.height
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostumeData':
        if isinstance(data, str):
            # Legacy format: just a path string
            import os
            name = os.path.splitext(os.path.basename(data))[0]
            return cls(name=name, path=data)
        return cls(
            name=data.get("name", "costume"),
            path=data.get("path", ""),
            draw_code=data.get("draw_code", ""),
            width=data.get("width", 32),
            height=data.get("height", 32)
        )

    def is_code_drawn(self) -> bool:
        """Check if this costume is code-drawn."""
        return bool(self.draw_code) and not self.path


@dataclass
class SpriteModel:
    """Data model for a sprite."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Sprite"
    class_name: str = "Sprite"

    # Transform
    x: float = 0.0
    y: float = 0.0
    direction: float = 90.0
    size: float = 1.0

    # Appearance - list of CostumeData
    costumes: List[CostumeData] = field(default_factory=list)
    current_costume: int = 0
    default_costume: int = 0  # Index of the default costume
    visible: bool = True
    color: tuple = (255, 100, 100)  # Default sprite color (RGB)

    # Collision
    collision_type: str = "rect"  # "rect", "circle", "mask"

    # Node type (scrawl_v2)
    node_type: str = "Sprite"  # Sprite, PhysicsSprite, RigidBody2D, KinematicBody2D, etc.

    # Physics properties
    is_physics: bool = False
    gravity_x: float = 0.0
    gravity_y: float = 0.2
    friction: float = 0.02  # 摩擦力系数 (0=无摩擦, 1=最大摩擦)
    elasticity: float = 0.8
    mass: float = 1.0
    linear_damping: float = 0.0
    angular_damping: float = 0.0

    # Camera2D properties
    camera_zoom: float = 1.0
    camera_smoothing: bool = True
    camera_smoothing_speed: float = 5.0
    camera_limit_left: float = -10000.0
    camera_limit_right: float = 10000.0
    camera_limit_top: float = -10000.0
    camera_limit_bottom: float = 10000.0
    camera_follow_target: str = ""  # Name of sprite to follow

    # Light2D properties
    light_color: tuple = (255, 255, 255)
    light_energy: float = 1.0
    light_radius: float = 200.0
    light_shadow: bool = False

    # Audio properties
    audio_stream: str = ""  # Path to audio file
    audio_volume: float = 1.0
    audio_pitch: float = 1.0
    audio_autoplay: bool = False
    audio_loop: bool = False

    # Particle properties
    particle_amount: int = 50
    particle_lifetime: float = 2.0
    particle_emitting: bool = True
    particle_preset: str = ""  # fire, smoke, explosion, etc.

    # UI properties
    ui_text: str = ""
    ui_font_size: int = 16
    ui_text_color: tuple = (255, 255, 255)
    ui_min_value: float = 0.0
    ui_max_value: float = 100.0
    ui_value: float = 100.0

    # Timer properties
    timer_wait_time: float = 1.0
    timer_one_shot: bool = False
    timer_autostart: bool = False

    # TileMap properties
    tilemap_cell_size: int = 32
    tilemap_data: str = ""  # Serialized tile data

    # Path/Line properties
    path_points: List[List[float]] = field(default_factory=list)
    path_loop: bool = False
    line_width: float = 2.0
    line_color: tuple = (255, 255, 255)

    # Navigation properties
    nav_max_speed: float = 200.0
    nav_target_x: float = 0.0
    nav_target_y: float = 0.0

    # Collision shape
    collision_shape: str = "rectangle"  # rectangle, circle, capsule
    collision_width: float = 32.0
    collision_height: float = 32.0
    collision_radius: float = 16.0

    # Inline code (the class definition)
    code: str = ""

    # Script path (legacy, for external scripts)
    script_path: Optional[str] = None

    # Custom properties
    properties: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_default(cls, name: str = "NewSprite", node_type: str = "Sprite") -> 'SpriteModel':
        """Create a new node with default values for the given type."""
        class_name = name.replace(" ", "")
        is_physics = node_type in PHYSICS_NODE_TYPES
        return cls(
            name=name,
            class_name=class_name,
            x=400.0,
            y=300.0,
            direction=90.0,
            size=1.0,
            visible=True,
            node_type=node_type,
            is_physics=is_physics,
            code=_default_node_code(class_name, node_type)
        )

    def add_costume(self, name: str, path: str) -> int:
        """Add or update a costume and return its index."""
        # Check if exists
        for i, c in enumerate(self.costumes):
            if c.name == name:
                c.path = path
                c.draw_code = "" # Clear code if switching to image
                return i
        
        costume = CostumeData(name=name, path=path)
        self.costumes.append(costume)
        return len(self.costumes) - 1

    def add_code_costume(self, name: str, width: int, height: int, draw_code: str) -> int:
        """Add or update a code-drawn costume and return its index."""
        # Check if exists
        for i, c in enumerate(self.costumes):
            if c.name == name:
                c.path = ""
                c.draw_code = draw_code
                c.width = width
                c.height = height
                return i

        costume = CostumeData(name=name, path="", draw_code=draw_code, width=width, height=height)
        self.costumes.append(costume)
        return len(self.costumes) - 1

    def get_current_costume_path(self) -> Optional[str]:
        """Get the path of the current costume."""
        if self.costumes and 0 <= self.current_costume < len(self.costumes):
            return self.costumes[self.current_costume].path
        return None

    def get_costume_by_name(self, name: str) -> Optional[CostumeData]:
        """Get a costume by name."""
        for costume in self.costumes:
            if costume.name == name:
                return costume
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        d = {
            "id": self.id,
            "name": self.name,
            "class": self.class_name,
            "pos": [self.x, self.y],
            "direction": self.direction,
            "size": self.size,
            "costumes": [c.to_dict() for c in self.costumes],
            "current_costume": self.current_costume,
            "default_costume": self.default_costume,
            "visible": self.visible,
            "color": list(self.color),
            "collision_type": self.collision_type,
            "node_type": self.node_type,
            "is_physics": self.is_physics,
            "gravity": [self.gravity_x, self.gravity_y],
            "friction": self.friction,
            "elasticity": self.elasticity,
            "mass": self.mass,
            "linear_damping": self.linear_damping,
            "angular_damping": self.angular_damping,
            "collision_shape": self.collision_shape,
            "collision_width": self.collision_width,
            "collision_height": self.collision_height,
            "collision_radius": self.collision_radius,
            "code": self.code,
            "script": self.script_path,
            "properties": self.properties,
        }
        # Node-type-specific data (only save non-default values)
        nt = self.node_type
        if nt == "Camera2D":
            d["camera"] = {
                "zoom": self.camera_zoom, "smoothing": self.camera_smoothing,
                "smoothing_speed": self.camera_smoothing_speed,
                "follow_target": self.camera_follow_target,
                "limits": [self.camera_limit_left, self.camera_limit_right,
                           self.camera_limit_top, self.camera_limit_bottom],
            }
        elif nt in ("PointLight2D", "DirectionalLight2D"):
            d["light"] = {
                "color": list(self.light_color), "energy": self.light_energy,
                "radius": self.light_radius, "shadow": self.light_shadow,
            }
        elif nt == "AudioPlayer2D":
            d["audio"] = {
                "stream": self.audio_stream, "volume": self.audio_volume,
                "pitch": self.audio_pitch, "autoplay": self.audio_autoplay,
                "loop": self.audio_loop,
            }
        elif nt == "ParticleEmitter2D":
            d["particle"] = {
                "amount": self.particle_amount, "lifetime": self.particle_lifetime,
                "emitting": self.particle_emitting, "preset": self.particle_preset,
            }
        elif nt in ("Label", "Button", "ProgressBar", "Panel"):
            d["ui"] = {
                "text": self.ui_text, "font_size": self.ui_font_size,
                "text_color": list(self.ui_text_color),
                "min_value": self.ui_min_value, "max_value": self.ui_max_value,
                "value": self.ui_value,
            }
        elif nt == "Timer":
            d["timer"] = {
                "wait_time": self.timer_wait_time, "one_shot": self.timer_one_shot,
                "autostart": self.timer_autostart,
            }
        elif nt == "TileMap":
            d["tilemap"] = {
                "cell_size": self.tilemap_cell_size, "data": self.tilemap_data,
            }
        elif nt in ("Path2D", "PathFollow2D", "Line2D"):
            d["path"] = {
                "points": self.path_points, "loop": self.path_loop,
                "line_width": self.line_width, "line_color": list(self.line_color),
            }
        elif nt == "NavigationAgent2D":
            d["nav"] = {
                "max_speed": self.nav_max_speed,
                "target": [self.nav_target_x, self.nav_target_y],
            }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpriteModel':
        """Create from dictionary."""
        pos = data.get("pos", [0, 0])
        class_name = data.get("class", "Sprite")
        node_type = data.get("node_type", "Sprite")

        # Handle costumes
        raw_costumes = data.get("costumes", [])
        costumes = [CostumeData.from_dict(c) for c in raw_costumes]

        # Handle color
        color = data.get("color", [255, 100, 100])
        if isinstance(color, list):
            color = tuple(color)

        # Handle gravity
        gravity = data.get("gravity", [0.0, 0.2])

        obj = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Sprite"),
            class_name=class_name,
            x=float(pos[0]) if len(pos) > 0 else 0.0,
            y=float(pos[1]) if len(pos) > 1 else 0.0,
            direction=float(data.get("direction", 90)),
            size=float(data.get("size", 1.0)),
            costumes=costumes,
            current_costume=data.get("current_costume", 0),
            default_costume=data.get("default_costume", 0),
            visible=data.get("visible", True),
            color=color,
            collision_type=data.get("collision_type", "rect"),
            node_type=node_type,
            is_physics=data.get("is_physics", False),
            gravity_x=float(gravity[0]) if len(gravity) > 0 else 0.0,
            gravity_y=float(gravity[1]) if len(gravity) > 1 else 0.2,
            friction=float(data.get("friction", 0.02)),
            elasticity=float(data.get("elasticity", 0.8)),
            mass=float(data.get("mass", 1.0)),
            linear_damping=float(data.get("linear_damping", 0.0)),
            angular_damping=float(data.get("angular_damping", 0.0)),
            collision_shape=data.get("collision_shape", "rectangle"),
            collision_width=float(data.get("collision_width", 32.0)),
            collision_height=float(data.get("collision_height", 32.0)),
            collision_radius=float(data.get("collision_radius", 16.0)),
            code=data.get("code", _default_node_code(class_name, node_type)),
            script_path=data.get("script"),
            properties=data.get("properties", {}),
        )

        # Load node-type-specific data
        cam = data.get("camera", {})
        if cam:
            obj.camera_zoom = float(cam.get("zoom", 1.0))
            obj.camera_smoothing = cam.get("smoothing", True)
            obj.camera_smoothing_speed = float(cam.get("smoothing_speed", 5.0))
            obj.camera_follow_target = cam.get("follow_target", "")
            limits = cam.get("limits", [-10000, 10000, -10000, 10000])
            obj.camera_limit_left = float(limits[0])
            obj.camera_limit_right = float(limits[1])
            obj.camera_limit_top = float(limits[2])
            obj.camera_limit_bottom = float(limits[3])

        light = data.get("light", {})
        if light:
            lc = light.get("color", [255, 255, 255])
            obj.light_color = tuple(lc) if isinstance(lc, list) else lc
            obj.light_energy = float(light.get("energy", 1.0))
            obj.light_radius = float(light.get("radius", 200.0))
            obj.light_shadow = light.get("shadow", False)

        audio = data.get("audio", {})
        if audio:
            obj.audio_stream = audio.get("stream", "")
            obj.audio_volume = float(audio.get("volume", 1.0))
            obj.audio_pitch = float(audio.get("pitch", 1.0))
            obj.audio_autoplay = audio.get("autoplay", False)
            obj.audio_loop = audio.get("loop", False)

        particle = data.get("particle", {})
        if particle:
            obj.particle_amount = int(particle.get("amount", 50))
            obj.particle_lifetime = float(particle.get("lifetime", 2.0))
            obj.particle_emitting = particle.get("emitting", True)
            obj.particle_preset = particle.get("preset", "")

        ui = data.get("ui", {})
        if ui:
            obj.ui_text = ui.get("text", "")
            obj.ui_font_size = int(ui.get("font_size", 16))
            tc = ui.get("text_color", [255, 255, 255])
            obj.ui_text_color = tuple(tc) if isinstance(tc, list) else tc
            obj.ui_min_value = float(ui.get("min_value", 0.0))
            obj.ui_max_value = float(ui.get("max_value", 100.0))
            obj.ui_value = float(ui.get("value", 100.0))

        timer = data.get("timer", {})
        if timer:
            obj.timer_wait_time = float(timer.get("wait_time", 1.0))
            obj.timer_one_shot = timer.get("one_shot", False)
            obj.timer_autostart = timer.get("autostart", False)

        tilemap = data.get("tilemap", {})
        if tilemap:
            obj.tilemap_cell_size = int(tilemap.get("cell_size", 32))
            obj.tilemap_data = tilemap.get("data", "")

        path = data.get("path", {})
        if path:
            obj.path_points = path.get("points", [])
            obj.path_loop = path.get("loop", False)
            obj.line_width = float(path.get("line_width", 2.0))
            lc2 = path.get("line_color", [255, 255, 255])
            obj.line_color = tuple(lc2) if isinstance(lc2, list) else lc2

        nav = data.get("nav", {})
        if nav:
            obj.nav_max_speed = float(nav.get("max_speed", 200.0))
            target = nav.get("target", [0, 0])
            obj.nav_target_x = float(target[0])
            obj.nav_target_y = float(target[1])

        return obj

    def clone(self) -> 'SpriteModel':
        """Create a copy of this sprite with a new ID."""
        new_sprite = SpriteModel.from_dict(self.to_dict())
        new_sprite.id = str(uuid.uuid4())
        new_sprite.name = f"{self.name}_copy"
        return new_sprite
