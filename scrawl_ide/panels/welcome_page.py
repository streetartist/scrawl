"""
Welcome Page

Welcome dialog shown when no project is open.
"""

import os
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush, QPen

from core.i18n import tr


class RecentFileItem(QWidget):
    """A clickable recent file item."""

    clicked = Signal(str)

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self._path = path
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Icon
        icon = QLabel("📁")
        icon.setStyleSheet("font-size: 24px; background: transparent;")
        layout.addWidget(icon)

        # File info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        name = os.path.basename(path)
        self._name_label = QLabel(name)
        self._name_label.setStyleSheet(
            "color: #E0E0E0; font-size: 13px; font-weight: bold; background: transparent;"
        )
        info_layout.addWidget(self._name_label)

        dir_path = os.path.dirname(path)
        self._path_label = QLabel(dir_path)
        self._path_label.setStyleSheet(
            "color: #78909C; font-size: 11px; background: transparent;"
        )
        info_layout.addWidget(self._path_label)

        layout.addLayout(info_layout, 1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        if self._hovered:
            painter.setBrush(QBrush(QColor("#3D5A6C")))
        else:
            painter.setBrush(QBrush(QColor("#2D3748")))
        painter.setPen(Qt.NoPen)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        painter.drawPath(path)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._path)


class WelcomePage(QDialog):
    """Welcome dialog shown when no project is open."""

    new_project_clicked = Signal()
    open_project_clicked = Signal()
    recent_file_clicked = Signal(str)
    exit_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recent_files = []
        self.setWindowTitle(tr("app.name"))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(720, 520)
        self._setup_ui()

    def reject(self):
        """Override reject to prevent closing via ESC."""
        pass

    def paintEvent(self, event):
        """Draw rounded rectangle background with shadow."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Shadow offset
        shadow = 10

        # Draw shadow
        for i in range(shadow):
            opacity = 30 - i * 3
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, opacity)))
            path = QPainterPath()
            path.addRoundedRect(
                shadow - i, shadow - i,
                self.width() - 2 * (shadow - i),
                self.height() - 2 * (shadow - i),
                12, 12
            )
            painter.drawPath(path)

        # Draw main background
        painter.setBrush(QBrush(QColor("#1E1E1E")))
        painter.setPen(QPen(QColor("#37474F"), 1))
        path = QPainterPath()
        path.addRoundedRect(
            shadow, shadow,
            self.width() - 2 * shadow,
            self.height() - 2 * shadow,
            12, 12
        )
        painter.drawPath(path)

    def _setup_ui(self):
        """Set up the welcome page UI."""
        # Main layout with margins for shadow
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Content container
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(24)

        # Header
        header = self._create_header()
        content_layout.addWidget(header)

        # Main content area
        main_content = QHBoxLayout()
        main_content.setSpacing(40)

        # Left side - Actions
        actions = self._create_actions()
        main_content.addWidget(actions)

        # Right side - Recent files
        recent = self._create_recent_section()
        main_content.addWidget(recent, 1)

        content_layout.addLayout(main_content, 1)

        # Footer
        footer = self._create_footer()
        content_layout.addWidget(footer)

        layout.addWidget(content_widget)

    def _create_header(self) -> QWidget:
        """Create the header section."""
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Title
        title = QLabel("Scrawl IDE")
        title.setStyleSheet(
            "color: #4FC3F7; font-size: 32px; font-weight: bold; background: transparent;"
        )
        header_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(tr("welcome.subtitle"))
        subtitle.setStyleSheet(
            "color: #90A4AE; font-size: 14px; background: transparent;"
        )
        header_layout.addWidget(subtitle)

        return header

    def _create_actions(self) -> QWidget:
        """Create the actions section."""
        actions = QWidget()
        actions.setStyleSheet("background: transparent;")
        actions.setFixedWidth(260)
        actions_layout = QVBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(12)

        # Section title
        title = QLabel(tr("welcome.start"))
        title.setStyleSheet(
            "color: #78909C; font-size: 11px; font-weight: bold; "
            "letter-spacing: 1px; background: transparent;"
        )
        actions_layout.addWidget(title)

        # New project button
        new_btn = self._create_action_button("📄", tr("welcome.new_project"))
        new_btn.clicked.connect(self.new_project_clicked.emit)
        actions_layout.addWidget(new_btn)

        # Open project button
        open_btn = self._create_action_button("📂", tr("welcome.open_project"))
        open_btn.clicked.connect(self.open_project_clicked.emit)
        actions_layout.addWidget(open_btn)

        actions_layout.addStretch()

        return actions

    def _create_action_button(self, icon: str, text: str) -> QPushButton:
        """Create a styled action button."""
        btn = QPushButton(f"  {icon}   {text}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(44)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #263238;
                border: 1px solid #37474F;
                border-radius: 8px;
                color: #E0E0E0;
                font-size: 14px;
                padding: 0 16px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #37474F;
                border-color: #4FC3F7;
            }
            QPushButton:pressed {
                background-color: #455A64;
            }
        """)
        return btn

    def _create_recent_section(self) -> QWidget:
        """Create the recent files section."""
        recent = QWidget()
        recent.setStyleSheet("background: transparent;")
        recent_layout = QVBoxLayout(recent)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(12)

        # Section title
        title = QLabel(tr("welcome.recent"))
        title.setStyleSheet(
            "color: #78909C; font-size: 11px; font-weight: bold; "
            "letter-spacing: 1px; background: transparent;"
        )
        recent_layout.addWidget(title)

        # Scroll area for recent files
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2D2D2D;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #546E7A;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #78909C;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self._recent_container = QWidget()
        self._recent_container.setStyleSheet("background: transparent;")
        self._recent_layout = QVBoxLayout(self._recent_container)
        self._recent_layout.setContentsMargins(0, 0, 4, 0)
        self._recent_layout.setSpacing(6)
        self._recent_layout.addStretch()

        scroll.setWidget(self._recent_container)
        recent_layout.addWidget(scroll, 1)

        return recent

    def _create_footer(self) -> QWidget:
        """Create the footer section."""
        footer = QWidget()
        footer.setStyleSheet("background: transparent;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)

        # Version info
        version = QLabel("Scrawl IDE v0.1.0")
        version.setStyleSheet(
            "color: #546E7A; font-size: 11px; background: transparent;"
        )
        footer_layout.addWidget(version)

        footer_layout.addStretch()

        # GitHub link
        github = QLabel(
            '<a href="https://github.com/streetartist/scrawl" '
            'style="color: #4FC3F7; text-decoration: none;">GitHub</a>'
        )
        github.setStyleSheet("font-size: 11px; background: transparent;")
        github.setOpenExternalLinks(True)
        footer_layout.addWidget(github)

        return footer

    def set_recent_files(self, files: list):
        """Set the list of recent files."""
        self._recent_files = files

        # Clear existing items
        while self._recent_layout.count() > 1:
            item = self._recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new items
        for path in files:
            if os.path.exists(path):
                item = RecentFileItem(path)
                item.clicked.connect(self.recent_file_clicked.emit)
                self._recent_layout.insertWidget(
                    self._recent_layout.count() - 1, item
                )

        # Show empty message if no recent files
        if not files or not any(os.path.exists(p) for p in files):
            empty = QLabel(tr("welcome.no_recent"))
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                "color: #546E7A; font-size: 13px; padding: 40px; background: transparent;"
            )
            self._recent_layout.insertWidget(0, empty)
