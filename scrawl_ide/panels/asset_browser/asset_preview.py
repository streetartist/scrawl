"""
Asset Preview

Preview widget for images and audio files.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QSlider, QStackedWidget, QScrollArea
)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QPixmap, QImage
from typing import Optional

from core.i18n import tr

# Try to import multimedia for audio preview
try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    MULTIMEDIA_AVAILABLE = False


class ImagePreview(QWidget):
    """Widget for previewing images."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Scroll area for large images
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setMinimumSize(100, 100)
        scroll.setWidget(self._image_label)

        layout.addWidget(scroll)

        # Info label
        self._info_label = QLabel()
        self._info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._info_label)

    def preview(self, path: str):
        """Preview an image file."""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._image_label.setText("Could not load image")
            self._info_label.clear()
            return

        # Scale if too large
        max_size = 400
        if pixmap.width() > max_size or pixmap.height() > max_size:
            pixmap = pixmap.scaled(
                max_size, max_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

        self._image_label.setPixmap(pixmap)

        # Show info
        original = QPixmap(path)
        self._info_label.setText(
            f"{original.width()} x {original.height()} px | "
            f"{os.path.getsize(path) / 1024:.1f} KB"
        )

    def clear(self):
        """Clear the preview."""
        self._image_label.clear()
        self._info_label.clear()


class AudioPreview(QWidget):
    """Widget for previewing audio files."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # File name
        self._name_label = QLabel()
        self._name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._name_label)

        if MULTIMEDIA_AVAILABLE:
            # Audio player
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)

            # Controls
            controls = QHBoxLayout()

            self._play_btn = QPushButton("Play")
            self._play_btn.clicked.connect(self._toggle_play)
            controls.addWidget(self._play_btn)

            self._stop_btn = QPushButton("Stop")
            self._stop_btn.clicked.connect(self._stop)
            controls.addWidget(self._stop_btn)

            layout.addLayout(controls)

            # Progress slider
            self._slider = QSlider(Qt.Horizontal)
            self._slider.sliderMoved.connect(self._seek)
            layout.addWidget(self._slider)

            # Connect player signals
            self._player.positionChanged.connect(self._on_position_changed)
            self._player.durationChanged.connect(self._on_duration_changed)
            self._player.playbackStateChanged.connect(self._on_state_changed)

        else:
            no_audio = QLabel(tr("asset.audio_unavailable"))
            no_audio.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_audio)

        # Info label
        self._info_label = QLabel()
        self._info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._info_label)

        layout.addStretch()

    def preview(self, path: str):
        """Preview an audio file."""
        self._name_label.setText(os.path.basename(path))

        if MULTIMEDIA_AVAILABLE:
            self._player.stop()
            self._player.setSource(QUrl.fromLocalFile(path))
            self._play_btn.setText("Play")

        # Show file size
        self._info_label.setText(f"{os.path.getsize(path) / 1024:.1f} KB")

    def clear(self):
        """Clear the preview."""
        if MULTIMEDIA_AVAILABLE:
            self._player.stop()
            self._player.setSource(QUrl())
        self._name_label.clear()
        self._info_label.clear()

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

    def _on_duration_changed(self, duration: int):
        """Handle duration change."""
        self._slider.setRange(0, duration)

    def _on_state_changed(self, state):
        """Handle playback state change."""
        if state == QMediaPlayer.PlayingState:
            self._play_btn.setText("Pause")
        else:
            self._play_btn.setText("Play")


class AssetPreview(QWidget):
    """Asset preview widget that shows appropriate preview for file type."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()

        # Empty state
        self._empty = QLabel(tr("asset.preview_empty"))
        self._empty.setAlignment(Qt.AlignCenter)
        self._stack.addWidget(self._empty)

        # Image preview
        self._image_preview = ImagePreview()
        self._stack.addWidget(self._image_preview)

        # Audio preview
        self._audio_preview = AudioPreview()
        self._stack.addWidget(self._audio_preview)

        # Text preview
        self._text_preview = QLabel()
        self._text_preview.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._text_preview.setWordWrap(True)
        self._text_preview.setMargin(8)
        text_scroll = QScrollArea()
        text_scroll.setWidget(self._text_preview)
        text_scroll.setWidgetResizable(True)
        self._stack.addWidget(text_scroll)

        layout.addWidget(self._stack)

    def preview(self, path: str):
        """Preview a file."""
        if not os.path.exists(path) or os.path.isdir(path):
            self._stack.setCurrentWidget(self._empty)
            return

        ext = os.path.splitext(path)[1].lower()

        if ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp'):
            self._image_preview.preview(path)
            self._stack.setCurrentWidget(self._image_preview)

        elif ext in ('.wav', '.mp3', '.ogg'):
            self._audio_preview.preview(path)
            self._stack.setCurrentWidget(self._audio_preview)

        elif ext in ('.py', '.txt', '.json', '.md'):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # First 1000 chars
                    if len(content) >= 1000:
                        content += "\n..."
                self._text_preview.setText(content)
            except (IOError, UnicodeDecodeError):
                self._text_preview.setText("Could not read file")
            self._stack.setCurrentIndex(3)  # Text preview

        else:
            self._empty.setText(tr("asset.preview_unavailable").format(ext=ext))
            self._stack.setCurrentWidget(self._empty)

    def clear(self):
        """Clear the preview."""
        self._image_preview.clear()
        self._audio_preview.clear()
        self._text_preview.clear()
        self._empty.setText(tr("asset.preview_empty"))
        self._stack.setCurrentWidget(self._empty)
