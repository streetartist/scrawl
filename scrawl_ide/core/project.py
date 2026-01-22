"""
Scrawl IDE Project Management

Handles project loading, saving, and management.
"""

import os
import json
from typing import Optional
from PySide6.QtCore import QObject, Signal

from models.project_model import ProjectModel


class Project(QObject):
    """Manages the current project state."""

    project_loaded = Signal(object)  # ProjectModel
    project_saved = Signal(str)  # path
    project_closed = Signal()
    project_modified = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model: Optional[ProjectModel] = None
        self._path: Optional[str] = None
        self._modified = False

    @property
    def model(self) -> Optional[ProjectModel]:
        return self._model

    @property
    def path(self) -> Optional[str]:
        return self._path

    @property
    def is_modified(self) -> bool:
        return self._modified

    @property
    def project_dir(self) -> Optional[str]:
        if self._path:
            return os.path.dirname(self._path)
        return None

    def new_project(self, path: str, name: str = "New Project"):
        """Create a new project."""
        self._model = ProjectModel.create_default(name)
        self._path = path
        self._modified = False

        # Create project directory structure
        project_dir = os.path.dirname(path)
        os.makedirs(os.path.join(project_dir, "assets", "images"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "assets", "sounds"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "scripts"), exist_ok=True)

        self.save()
        self.project_loaded.emit(self._model)

    def open_project(self, path: str) -> bool:
        """Open an existing project."""
        if not os.path.exists(path):
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._model = ProjectModel.from_dict(data)
            self._path = path
            self._modified = False
            self.project_loaded.emit(self._model)
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading project: {e}")
            return False

    def save(self) -> bool:
        """Save the current project."""
        if not self._model or not self._path:
            return False

        try:
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump(self._model.to_dict(), f, indent=2, ensure_ascii=False)

            self._modified = False
            self.project_saved.emit(self._path)
            return True
        except IOError as e:
            print(f"Error saving project: {e}")
            return False

    def save_as(self, path: str) -> bool:
        """Save the project to a new path."""
        old_path = self._path
        self._path = path

        if not self.save():
            self._path = old_path
            return False

        return True

    def close(self):
        """Close the current project."""
        self._model = None
        self._path = None
        self._modified = False
        self.project_closed.emit()

    def mark_modified(self):
        """Mark the project as modified."""
        if not self._modified:
            self._modified = True
            self.project_modified.emit()
