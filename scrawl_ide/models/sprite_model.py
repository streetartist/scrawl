"""
Sprite Data Model

Represents a sprite in the Scrawl IDE.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid


def _default_sprite_code(class_name: str = "MySprite") -> str:
    """Generate default sprite class code."""
    return f'''class {class_name}(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "{class_name}"

    @as_main
    def main_loop(self):
        """主循环"""
        while True:
            # 在这里添加逻辑
            yield 0
'''


@dataclass
class CostumeData:
    """Data for a single costume."""
    name: str
    path: str

    def to_dict(self) -> Dict[str, str]:
        return {"name": self.name, "path": self.path}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostumeData':
        if isinstance(data, str):
            # Legacy format: just a path string
            import os
            name = os.path.splitext(os.path.basename(data))[0]
            return cls(name=name, path=data)
        return cls(name=data.get("name", "costume"), path=data.get("path", ""))


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

    # Inline code (the class definition)
    code: str = ""

    # Script path (legacy, for external scripts)
    script_path: Optional[str] = None

    # Use physics sprite
    is_physics: bool = False

    # Custom properties
    properties: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_default(cls, name: str = "NewSprite") -> 'SpriteModel':
        """Create a new sprite with default values."""
        class_name = name.replace(" ", "")
        return cls(
            name=name,
            class_name=class_name,
            x=400.0,
            y=300.0,
            direction=90.0,
            size=1.0,
            visible=True,
            code=_default_sprite_code(class_name)
        )

    def add_costume(self, name: str, path: str) -> int:
        """Add a costume and return its index."""
        costume = CostumeData(name=name, path=path)
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
        return {
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
            "code": self.code,
            "script": self.script_path,
            "is_physics": self.is_physics,
            "properties": self.properties
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpriteModel':
        """Create from dictionary."""
        pos = data.get("pos", [0, 0])
        class_name = data.get("class", "Sprite")

        # Handle costumes - could be old format (list of strings) or new format (list of dicts)
        raw_costumes = data.get("costumes", [])
        costumes = [CostumeData.from_dict(c) for c in raw_costumes]

        return cls(
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
            code=data.get("code", _default_sprite_code(class_name)),
            script_path=data.get("script"),
            is_physics=data.get("is_physics", False),
            properties=data.get("properties", {})
        )

    def clone(self) -> 'SpriteModel':
        """Create a copy of this sprite with a new ID."""
        new_sprite = SpriteModel.from_dict(self.to_dict())
        new_sprite.id = str(uuid.uuid4())
        new_sprite.name = f"{self.name}_copy"
        return new_sprite
