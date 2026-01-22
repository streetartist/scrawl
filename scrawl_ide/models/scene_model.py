"""
Scene Data Model

Represents a scene in the Scrawl IDE.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
import uuid

from .sprite_model import SpriteModel


@dataclass
class SceneModel:
    """Data model for a scene."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Scene"

    # Background
    background_color: Tuple[int, int, int] = (100, 150, 200)
    background_image: Optional[str] = None

    # Sprites in this scene
    sprites: List[SpriteModel] = field(default_factory=list)

    @classmethod
    def create_default(cls, name: str = "MainScene") -> 'SceneModel':
        """Create a new scene with default values."""
        return cls(
            name=name,
            background_color=(100, 150, 200)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "background_color": list(self.background_color),
            "background_image": self.background_image,
            "sprites": [sprite.to_dict() for sprite in self.sprites]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneModel':
        """Create from dictionary."""
        bg_color = data.get("background_color", [100, 150, 200])
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Scene"),
            background_color=tuple(bg_color) if isinstance(bg_color, list) else bg_color,
            background_image=data.get("background_image"),
            sprites=[SpriteModel.from_dict(s) for s in data.get("sprites", [])]
        )

    def add_sprite(self, sprite: SpriteModel):
        """Add a sprite to the scene."""
        self.sprites.append(sprite)

    def remove_sprite(self, sprite_id: str) -> Optional[SpriteModel]:
        """Remove a sprite by ID."""
        for i, sprite in enumerate(self.sprites):
            if sprite.id == sprite_id:
                return self.sprites.pop(i)
        return None

    def get_sprite(self, sprite_id: str) -> Optional[SpriteModel]:
        """Get a sprite by ID."""
        for sprite in self.sprites:
            if sprite.id == sprite_id:
                return sprite
        return None

    def get_sprite_by_name(self, name: str) -> Optional[SpriteModel]:
        """Get a sprite by name."""
        for sprite in self.sprites:
            if sprite.name == name:
                return sprite
        return None
