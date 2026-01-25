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

    def clear_window_state(self):
        """Clear saved window geometry and state to reset layout."""
        self._settings.remove("window/geometry")
        self._settings.remove("window/state")

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

    def remove_recent_project(self, path: str):
        recent = self.get_recent_projects()
        if path in recent:
            recent.remove(path)
            self._settings.setValue("projects/recent", recent)

    # Aliases for recent files
    def get_recent_files(self) -> list:
        return self.get_recent_projects()

    def add_recent_file(self, path: str):
        self.add_recent_project(path)

    def remove_recent_file(self, path: str):
        self.remove_recent_project(path)

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
        # Default to good cross-platform monospace fonts
        from PySide6.QtGui import QFontDatabase

        # Preferred fonts in order (good for code, compatible with DirectWrite)
        preferred = [
            "Cascadia Code",    # Modern, ligatures support
            "Cascadia Mono",    # Cascadia without ligatures
            "JetBrains Mono",   # Great for coding
            "Fira Code",        # Popular with ligatures
            "Source Code Pro",  # Adobe's coding font
            "Consolas",         # Windows default
            "Monaco",           # macOS
            "DejaVu Sans Mono", # Linux
            "Courier New",      # Fallback
        ]

        # Fonts known to have issues with DirectWrite
        problematic_fonts = {"Fixedsys", "Terminal", "System"}

        # Check saved setting
        saved = self._settings.value("editor/font_family")
        if saved and saved not in problematic_fonts:
            # Verify font exists and is usable
            if saved in QFontDatabase.families():
                return saved

        # Find best available font
        available = set(QFontDatabase.families())
        for font in preferred:
            if font in available:
                return font

        return "Consolas"

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

    # AI settings
    def get_ai_api_key(self) -> str:
        return self._settings.value("ai/api_key", "")

    def set_ai_api_key(self, key: str):
        self._settings.setValue("ai/api_key", key)

    def get_ai_endpoint(self) -> str:
        return self._settings.value("ai/endpoint", "https://api.openai.com/v1")

    def set_ai_endpoint(self, endpoint: str):
        self._settings.setValue("ai/endpoint", endpoint)

    def get_ai_model(self) -> str:
        return self._settings.value("ai/model", "gpt-4o-mini")

    def set_ai_model(self, model: str):
        self._settings.setValue("ai/model", model)
