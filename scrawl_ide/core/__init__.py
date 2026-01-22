"""Core modules for Scrawl IDE."""

from .application import ScrawlApplication
from .main_window import MainWindow
from .settings import Settings
from .project import Project
from .i18n import Translator, tr

__all__ = ['ScrawlApplication', 'MainWindow', 'Settings', 'Project', 'Translator', 'tr']
