"""
Sprite Data Model

Represents a sprite in the Scrawl IDE.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid


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

    # Appearance
    costumes: List[str] = field(default_factory=list)
    current_costume: int = 0
    visible: bool = True

    # Script
    script_path: Optional[str] = None

    # Custom properties
    properties: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_default(cls, name: str = "NewSprite") -> 'SpriteModel':
        """Create a new sprite with default values."""
        return cls(
            name=name,
            class_name=name.replace(" ", ""),
            x=400.0,
            y=300.0,
            direction=90.0,
            size=1.0,
            visible=True
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "class": self.class_name,
            "pos": [self.x, self.y],
            "direction": self.direction,
            "size": self.size,
            "costumes": self.costumes,
            "current_costume": self.current_costume,
            "visible": self.visible,
            "script": self.script_path,
            "properties": self.properties
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpriteModel':
        """Create from dictionary."""
        pos = data.get("pos", [0, 0])
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Sprite"),
            class_name=data.get("class", "Sprite"),
            x=float(pos[0]) if len(pos) > 0 else 0.0,
            y=float(pos[1]) if len(pos) > 1 else 0.0,
            direction=float(data.get("direction", 90)),
            size=float(data.get("size", 1.0)),
            costumes=data.get("costumes", []),
            current_costume=data.get("current_costume", 0),
            visible=data.get("visible", True),
            script_path=data.get("script"),
            properties=data.get("properties", {})
        )

    def clone(self) -> 'SpriteModel':
        """Create a copy of this sprite with a new ID."""
        new_sprite = SpriteModel.from_dict(self.to_dict())
        new_sprite.id = str(uuid.uuid4())
        new_sprite.name = f"{self.name}_copy"
        return new_sprite
