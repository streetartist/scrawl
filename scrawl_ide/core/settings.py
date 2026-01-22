"""
Scrawl IDE Settings Management

Handles application settings persistence using QSettings.
"""

from PySide6.QtCore import QSettings, QByteArray
from typing import Any, Optional


class Settings:
    """Application settings manager using QSettings."""

    _instance: Optional['Settings'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = QSettings()
        return cls._instance

    @property
    def settings(self) -> QSettings:
        return self._settings

    # Window geometry
    def save_window_geometry(self, geometry: QByteArray):
        self._settings.setValue("window/geometry", geometry)

    def load_window_geometry(self) -> Optional[QByteArray]:
        return self._settings.value("window/geometry")

    def save_window_state(self, state: QByteArray):
        self._settings.setValue("window/state", state)

    def load_window_state(self) -> Optional[QByteArray]:
        return self._settings.value("window/state")

    # Recent projects
    def get_recent_projects(self) -> list:
        return self._settings.value("projects/recent", []) or []

    def add_recent_project(self, path: str):
        recent = self.get_recent_projects()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:10]  # Keep only 10 most recent
        self._settings.setValue("projects/recent", recent)

    def get_last_project(self) -> Optional[str]:
        return self._settings.value("projects/last")

    def set_last_project(self, path: str):
        self._settings.setValue("projects/last", path)

    # Editor settings
    def get_font_size(self) -> int:
        return int(self._settings.value("editor/font_size", 12))

    def set_font_size(self, size: int):
        self._settings.setValue("editor/font_size", size)

    def get_font_family(self) -> str:
        return self._settings.value("editor/font_family", "Consolas")

    def set_font_family(self, family: str):
        self._settings.setValue("editor/font_family", family)

    def get_tab_width(self) -> int:
        return int(self._settings.value("editor/tab_width", 4))

    def set_tab_width(self, width: int):
        self._settings.setValue("editor/tab_width", width)

    def get_use_spaces(self) -> bool:
        return self._settings.value("editor/use_spaces", True) in [True, "true"]

    def set_use_spaces(self, use_spaces: bool):
        self._settings.setValue("editor/use_spaces", use_spaces)

    # Language settings
    def get_language(self) -> str:
        """Get the current language. Default is Chinese (zh_CN)."""
        return self._settings.value("app/language", "zh_CN")

    def set_language(self, language: str):
        """Set the application language."""
        self._settings.setValue("app/language", language)

    # General settings
    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.value(key, default)

    def set(self, key: str, value: Any):
        self._settings.setValue(key, value)
