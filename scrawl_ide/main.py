"""
Scrawl IDE - Main Entry Point

A visual IDE for the Scrawl game engine, built with PySide6.
"""

import sys
from core.application import ScrawlApplication
from core.main_window import MainWindow


def main():
    """Main entry point for Scrawl IDE."""
    app = ScrawlApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
