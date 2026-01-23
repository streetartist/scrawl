"""
Scrawl IDE Application Configuration

Handles QApplication setup with high DPI support and application-wide settings.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import os


class ScrawlApplication(QApplication):
    """Custom QApplication with Scrawl IDE configuration."""

    def __init__(self, argv):
        # Enable high DPI scaling
        super().__init__(argv)

        self.setApplicationName("Scrawl IDE")
        self.setApplicationVersion("0.2.1")
        self.setOrganizationName("Scrawl")
        self.setOrganizationDomain("scrawl.dev")

        # Set default font with Chinese support
        font = QFont("Microsoft YaHei UI", 9)
        font.setStyleHint(QFont.SansSerif)
        self.setFont(font)

        # Load stylesheet
        self._load_stylesheet()

    def _load_stylesheet(self):
        """Load the application stylesheet."""
        style_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources", "styles", "dark_theme.qss"
        )

        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
