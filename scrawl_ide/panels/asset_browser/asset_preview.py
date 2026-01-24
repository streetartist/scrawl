"""
Asset Preview

Preview widget for images, audio, and text files with improved UI.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QSlider, QStackedWidget, QScrollArea, QFrame, QToolButton,
    QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QBrush, QFont
from typing import Optional

from core.i18n import tr

# Try to import multimedia for audio preview
try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    MULTIMEDIA_AVAILABLE = False


class FileInfoHeader(QFrame):
    """Header widget showing file name and info."""

    copy_path_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FileInfoHeader")
        self._path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # File name with icon
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(24, 24)
        name_layout.addWidget(self._icon_label)

        self._name_label = QLabel()
        self._name_label.setObjectName("FileName")
        name_layout.addWidget(self._name_label, 1)

        # Copy path button
        self._copy_btn = QToolButton()
        self._copy_btn.setText("📋")
        self._copy_btn.setToolTip("Copy path")
        self._copy_btn.clicked.connect(self._on_copy_path)
        name_layout.addWidget(self._copy_btn)

        layout.addLayout(name_layout)

        # File info (size, dimensions, etc.)
        self._info_label = QLabel()
        self._info_label.setObjectName("FileInfo")
        layout.addWidget(self._info_label)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            #FileInfoHeader {
                background-color: #263238;
                border-radius: 6px;
                margin: 4px;
            }
            #FileName {
                color: #E0E0E0;
                font-weight: bold;
                font-size: 13px;
            }
            #FileInfo {
                color: #90A4AE;
                font-size: 11px;
            }
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #37474F;
            }
        """)

    def set_file(self, path: str, icon: str = "📄", info: str = ""):
        """Set the file info to display."""
        self._path = path
        name = os.path.basename(path)
        self._name_label.setText(name)
        self._icon_label.setText(icon)
        self._info_label.setText(info)

    def _on_copy_path(self):
        """Copy file path to clipboard."""
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._path)
        # Show feedback
        original_text = self._copy_btn.text()
        self._copy_btn.setText("✓")
        QTimer.singleShot(1000, lambda: self._copy_btn.setText(original_text))


class ImagePreview(QWidget):
    """Widget for previewing images with checkerboard background."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Header
        self._header = FileInfoHeader()
        layout.addWidget(self._header)

        # Image container with checkerboard background
        self._image_container = QFrame()
        self._image_container.setObjectName("ImageContainer")
        container_layout = QVBoxLayout(self._image_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for large images
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setObjectName("ImageScroll")

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setMinimumSize(100, 100)
        scroll.setWidget(self._image_label)

        container_layout.addWidget(scroll)
        layout.addWidget(self._image_container, 1)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            #ImageContainer {
                background-color: #1E1E1E;
                border-radius: 6px;
                margin: 4px;
            }
            #ImageScroll {
                background-color: transparent;
                border: none;
            }
            #ImageScroll QWidget {
                background-color: transparent;
            }
        """)

    def _create_checkerboard_pixmap(self, size: QSize) -> QPixmap:
        """Create a checkerboard pattern for transparency."""
        pixmap = QPixmap(size)
        painter = QPainter(pixmap)

        cell_size = 8
        light = QColor('#3A3A3A')
        dark = QColor('#2A2A2A')

        for y in range(0, size.height(), cell_size):
            for x in range(0, size.width(), cell_size):
                color = light if (x // cell_size + y // cell_size) % 2 == 0 else dark
                painter.fillRect(x, y, cell_size, cell_size, color)

        painter.end()
        return pixmap

    def preview(self, path: str):
        """Preview an image file."""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._image_label.setText("Could not load image")
            self._header.set_file(path, "🖼️", "Error loading image")
            return

        original_size = pixmap.size()

        # Scale if too large
        max_size = 400
        display_pixmap = pixmap
        if pixmap.width() > max_size or pixmap.height() > max_size:
            display_pixmap = pixmap.scaled(
                max_size, max_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

        # Create checkerboard background for transparency
        if pixmap.hasAlphaChannel():
            bg = self._create_checkerboard_pixmap(display_pixmap.size())
            painter = QPainter(bg)
            painter.drawPixmap(0, 0, display_pixmap)
            painter.end()
            display_pixmap = bg

        self._image_label.setPixmap(display_pixmap)

        # Update header
        file_size = os.path.getsize(path) / 1024
        info = f"{original_size.width()} × {original_size.height()} px  •  {file_size:.1f} KB"
        self._header.set_file(path, "🖼️", info)

    def clear(self):
        """Clear the preview."""
        self._image_label.clear()


class AudioPreview(QWidget):
    """Widget for previewing audio files with improved UI."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Header
        self._header = FileInfoHeader()
        layout.addWidget(self._header)

        # Player container
        player_container = QFrame()
        player_container.setObjectName("AudioPlayer")
        player_layout = QVBoxLayout(player_container)
        player_layout.setContentsMargins(16, 16, 16, 16)
        player_layout.setSpacing(12)

        if MULTIMEDIA_AVAILABLE:
            # Audio player
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)

            # Waveform placeholder (visual element)
            waveform = QLabel("🎵")
            waveform.setAlignment(Qt.AlignCenter)
            waveform.setStyleSheet("font-size: 48px;")
            player_layout.addWidget(waveform)

            # Progress slider
            self._slider = QSlider(Qt.Horizontal)
            self._slider.setObjectName("AudioSlider")
            self._slider.sliderMoved.connect(self._seek)
            player_layout.addWidget(self._slider)

            # Time labels
            time_layout = QHBoxLayout()
            self._current_time = QLabel("0:00")
            self._current_time.setObjectName("TimeLabel")
            time_layout.addWidget(self._current_time)
            time_layout.addStretch()
            self._total_time = QLabel("0:00")
            self._total_time.setObjectName("TimeLabel")
            time_layout.addWidget(self._total_time)
            player_layout.addLayout(time_layout)

            # Controls
            controls = QHBoxLayout()
            controls.setSpacing(8)
            controls.addStretch()

            self._play_btn = QPushButton("▶")
            self._play_btn.setObjectName("PlayButton")
            self._play_btn.setFixedSize(48, 48)
            self._play_btn.clicked.connect(self._toggle_play)
            controls.addWidget(self._play_btn)

            self._stop_btn = QPushButton("⏹")
            self._stop_btn.setObjectName("StopButton")
            self._stop_btn.setFixedSize(36, 36)
            self._stop_btn.clicked.connect(self._stop)
            controls.addWidget(self._stop_btn)

            controls.addStretch()
            player_layout.addLayout(controls)

            # Connect player signals
            self._player.positionChanged.connect(self._on_position_changed)
            self._player.durationChanged.connect(self._on_duration_changed)
            self._player.playbackStateChanged.connect(self._on_state_changed)

        else:
            no_audio = QLabel(tr("asset.audio_unavailable"))
            no_audio.setAlignment(Qt.AlignCenter)
            no_audio.setWordWrap(True)
            player_layout.addWidget(no_audio)

        layout.addWidget(player_container, 1)
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            #AudioPlayer {
                background-color: #263238;
                border-radius: 8px;
                margin: 4px;
            }
            #AudioSlider {
                height: 20px;
            }
            #AudioSlider::groove:horizontal {
                background: #37474F;
                height: 6px;
                border-radius: 3px;
            }
            #AudioSlider::handle:horizontal {
                background: #4FC3F7;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            #AudioSlider::sub-page:horizontal {
                background: #4FC3F7;
                border-radius: 3px;
            }
            #TimeLabel {
                color: #90A4AE;
                font-size: 11px;
            }
            #PlayButton {
                background-color: #4FC3F7;
                border: none;
                border-radius: 24px;
                color: #1E1E1E;
                font-size: 18px;
                font-weight: bold;
            }
            #PlayButton:hover {
                background-color: #81D4FA;
            }
            #StopButton {
                background-color: #455A64;
                border: none;
                border-radius: 18px;
                color: #E0E0E0;
                font-size: 14px;
            }
            #StopButton:hover {
                background-color: #546E7A;
            }
        """)

    def _format_time(self, ms: int) -> str:
        """Format milliseconds as M:SS."""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def preview(self, path: str):
        """Preview an audio file."""
        file_size = os.path.getsize(path) / 1024
        ext = os.path.splitext(path)[1].upper()[1:]
        info = f"{ext}  •  {file_size:.1f} KB"
        self._header.set_file(path, "🎵", info)

        if MULTIMEDIA_AVAILABLE:
            self._player.stop()
            self._player.setSource(QUrl.fromLocalFile(path))
            self._play_btn.setText("▶")
            self._current_time.setText("0:00")
            self._total_time.setText("0:00")

    def clear(self):
        """Clear the preview."""
        if MULTIMEDIA_AVAILABLE:
            self._player.stop()
            self._player.setSource(QUrl())

    def _toggle_play(self):
        """Toggle play/pause."""
        if not MULTIMEDIA_AVAILABLE:
            return

        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _stop(self):
        """Stop playback."""
        if MULTIMEDIA_AVAILABLE:
            self._player.stop()

    def _seek(self, position: int):
        """Seek to position."""
        if MULTIMEDIA_AVAILABLE:
            self._player.setPosition(position)

    def _on_position_changed(self, position: int):
        """Handle position change."""
        self._slider.blockSignals(True)
        self._slider.setValue(position)
        self._slider.blockSignals(False)
        self._current_time.setText(self._format_time(position))

    def _on_duration_changed(self, duration: int):
        """Handle duration change."""
        self._slider.setRange(0, duration)
        self._total_time.setText(self._format_time(duration))

    def _on_state_changed(self, state):
        """Handle playback state change."""
        if state == QMediaPlayer.PlayingState:
            self._play_btn.setText("⏸")
        else:
            self._play_btn.setText("▶")


class TextPreview(QWidget):
    """Widget for previewing text/code files."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Header
        self._header = FileInfoHeader()
        layout.addWidget(self._header)

        # Text container
        text_container = QFrame()
        text_container.setObjectName("TextContainer")
        container_layout = QVBoxLayout(text_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("TextScroll")

        self._text_label = QLabel()
        self._text_label.setObjectName("TextContent")
        self._text_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._text_label.setWordWrap(True)
        self._text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._text_label.setMargin(12)
        scroll.setWidget(self._text_label)

        container_layout.addWidget(scroll)
        layout.addWidget(text_container, 1)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            #TextContainer {
                background-color: #1E1E1E;
                border-radius: 6px;
                margin: 4px;
            }
            #TextScroll {
                background-color: transparent;
                border: none;
            }
            #TextContent {
                background-color: transparent;
                color: #E0E0E0;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 12px;
            }
        """)

    def preview(self, path: str):
        """Preview a text file."""
        ext = os.path.splitext(path)[1].lower()
        icon = "🐍" if ext == ".py" else "📋" if ext == ".json" else "📄"

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # First 2000 chars
                lines = content.count('\n') + 1
                if len(content) >= 2000:
                    content += "\n\n... (truncated)"

            file_size = os.path.getsize(path) / 1024
            info = f"{lines} lines  •  {file_size:.1f} KB"
            self._header.set_file(path, icon, info)
            self._text_label.setText(content)

        except (IOError, UnicodeDecodeError) as e:
            self._header.set_file(path, "❌", "Error reading file")
            self._text_label.setText(f"Could not read file: {e}")

    def clear(self):
        """Clear the preview."""
        self._text_label.clear()


class AssetPreview(QWidget):
    """Asset preview widget that shows as a floating panel."""

    closed = Signal()  # Emitted when close button clicked

    def __init__(self, parent=None):
        # Don't pass parent to make it a top-level window
        super().__init__(None)

        # Make it a floating popup window (not on top of other apps)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setFixedSize(300, 350)

        self._parent = parent  # Store reference to parent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # Main container with border
        container = QFrame()
        container.setObjectName("PreviewContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header with close button
        header = QFrame()
        header.setObjectName("PreviewHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 4, 4)

        header_label = QLabel("Preview")
        header_label.setStyleSheet("color: #90A4AE; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.setObjectName("PreviewCloseBtn")
        close_btn.setToolTip("Close preview")
        close_btn.clicked.connect(self._on_close)
        header_layout.addWidget(close_btn)

        container_layout.addWidget(header)

        self._stack = QStackedWidget()

        # Empty state
        empty_widget = QFrame()
        empty_widget.setObjectName("EmptyPreview")
        empty_layout = QVBoxLayout(empty_widget)
        self._empty_icon = QLabel("📁")
        self._empty_icon.setAlignment(Qt.AlignCenter)
        self._empty_icon.setStyleSheet("font-size: 48px; color: #546E7A;")
        empty_layout.addWidget(self._empty_icon)
        self._empty_label = QLabel(tr("asset.preview_empty"))
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: #78909C; font-size: 12px;")
        empty_layout.addWidget(self._empty_label)
        self._stack.addWidget(empty_widget)

        # Image preview
        self._image_preview = ImagePreview()
        self._stack.addWidget(self._image_preview)

        # Audio preview
        self._audio_preview = AudioPreview()
        self._stack.addWidget(self._audio_preview)

        # Text preview
        self._text_preview = TextPreview()
        self._stack.addWidget(self._text_preview)

        container_layout.addWidget(self._stack)
        layout.addWidget(container)

        self._apply_styles()

    def _on_close(self):
        """Handle close button click."""
        self.hide()
        self.closed.emit()

    def showAtPosition(self, global_pos):
        """Show the preview at a specific global position."""
        self.move(global_pos.x(), global_pos.y())
        self.show()

    def _apply_styles(self):
        self.setStyleSheet("""
            #PreviewContainer {
                background-color: #1E1E1E;
                border: 1px solid #4FC3F7;
                border-radius: 8px;
            }
            #PreviewHeader {
                background-color: #263238;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid #37474F;
            }
            #PreviewCloseBtn {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 2px 6px;
                color: #78909C;
                font-size: 12px;
            }
            #PreviewCloseBtn:hover {
                background-color: #37474F;
                color: #E0E0E0;
            }
            #EmptyPreview {
                background-color: #1E1E1E;
            }
        """)

    def preview(self, path: str):
        """Preview a file."""
        if not os.path.exists(path) or os.path.isdir(path):
            self._stack.setCurrentIndex(0)
            return

        ext = os.path.splitext(path)[1].lower()

        if ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'):
            self._image_preview.preview(path)
            self._stack.setCurrentWidget(self._image_preview)

        elif ext in ('.wav', '.mp3', '.ogg'):
            self._audio_preview.preview(path)
            self._stack.setCurrentWidget(self._audio_preview)

        elif ext in ('.py', '.txt', '.json', '.md'):
            self._text_preview.preview(path)
            self._stack.setCurrentWidget(self._text_preview)

        else:
            self._empty_icon.setText("📄")
            self._empty_label.setText(tr("asset.preview_unavailable").format(ext=ext))
            self._stack.setCurrentIndex(0)

    def clear(self):
        """Clear the preview."""
        self._image_preview.clear()
        self._audio_preview.clear()
        self._text_preview.clear()
        self._empty_icon.setText("📁")
        self._empty_label.setText(tr("asset.preview_empty"))
        self._stack.setCurrentIndex(0)
