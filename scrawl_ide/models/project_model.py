"""
Project Data Model

Represents a Scrawl project.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .scene_model import SceneModel


@dataclass
class GameSettings:
    """Game settings configuration."""

    width: int = 800
    height: int = 600
    title: str = "My Game"
    fps: int = 60
    fullscreen: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "title": self.title,
            "fps": self.fps,
            "fullscreen": self.fullscreen
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSettings':
        return cls(
            width=data.get("width", 800),
            height=data.get("height", 600),
            title=data.get("title", "My Game"),
            fps=data.get("fps", 60),
            fullscreen=data.get("fullscreen", False)
        )


@dataclass
class ProjectModel:
    """Data model for a Scrawl project."""

    name: str = "New Project"
    version: str = "1.0"

    # Game settings
    game: GameSettings = field(default_factory=GameSettings)

    # Scenes
    scenes: List[SceneModel] = field(default_factory=list)

    # Script mappings (class_name -> script_path)
    scripts: Dict[str, str] = field(default_factory=dict)

    # Asset lists
    images: List[str] = field(default_factory=list)
    sounds: List[str] = field(default_factory=list)

    @classmethod
    def create_default(cls, name: str = "New Project") -> 'ProjectModel':
        """Create a new project with default values."""
        project = cls(
            name=name,
            game=GameSettings(title=name),
            scenes=[SceneModel.create_default("MainScene")]
        )
        return project

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "game": self.game.to_dict(),
            "scenes": [scene.to_dict() for scene in self.scenes],
            "scripts": self.scripts,
            "assets": {
                "images": self.images,
                "sounds": self.sounds
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectModel':
        """Create from dictionary."""
        assets = data.get("assets", {})
        return cls(
            name=data.get("name", "Project"),
            version=data.get("version", "1.0"),
            game=GameSettings.from_dict(data.get("game", {})),
            scenes=[SceneModel.from_dict(s) for s in data.get("scenes", [])],
            scripts=data.get("scripts", {}),
            images=assets.get("images", []),
            sounds=assets.get("sounds", [])
        )

    def get_scene(self, name: str) -> Optional[SceneModel]:
        """Get a scene by name."""
        for scene in self.scenes:
            if scene.name == name:
                return scene
        return None

    def get_scene_by_id(self, scene_id: str) -> Optional[SceneModel]:
        """Get a scene by ID."""
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        return None

    def add_scene(self, scene: SceneModel):
        """Add a scene to the project."""
        self.scenes.append(scene)

    def remove_scene(self, scene_id: str) -> Optional[SceneModel]:
        """Remove a scene by ID."""
        for i, scene in enumerate(self.scenes):
            if scene.id == scene_id:
                return self.scenes.pop(i)
        return None
