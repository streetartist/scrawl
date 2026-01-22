"""
Scene Graphics Items

QGraphicsItem implementations for sprites and other scene elements.
"""

from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsPixmapItem,
    QGraphicsEllipseItem, QStyleOptionGraphicsItem, QWidget
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPixmap, QTransform
)
from typing import Optional
import os

from models import SpriteModel


class SpriteItem(QGraphicsItem):
    """A graphics item representing a sprite in the scene."""

    HANDLE_SIZE = 8
    HANDLE_HALF = 4

    def __init__(self, sprite_model: SpriteModel, parent=None):
        super().__init__(parent)

        self.sprite_model = sprite_model
        self._pixmap: Optional[QPixmap] = None
        self._selected = False
        self._resizing = False
        self._resize_handle = None

        # Default size when no costume
        self._default_width = 64
        self._default_height = 64

        # Enable interactions
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        # Set position from model
        self.setPos(sprite_model.x, sprite_model.y)

        # Load costume if available
        self._load_costume()

    def _load_costume(self):
        """Load the sprite's current costume."""
        if self.sprite_model.costumes:
            costume_path = self.sprite_model.costumes[self.sprite_model.current_costume]
            if os.path.exists(costume_path):
                self._pixmap = QPixmap(costume_path)

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle."""
        if self._pixmap and not self._pixmap.isNull():
            w = self._pixmap.width() * self.sprite_model.size
            h = self._pixmap.height() * self.sprite_model.size
        else:
            w = self._default_width * self.sprite_model.size
            h = self._default_height * self.sprite_model.size

        # Add space for selection handles
        margin = self.HANDLE_SIZE
        return QRectF(-w/2 - margin, -h/2 - margin, w + margin*2, h + margin*2)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the sprite."""
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate dimensions
        if self._pixmap and not self._pixmap.isNull():
            w = self._pixmap.width() * self.sprite_model.size
            h = self._pixmap.height() * self.sprite_model.size
        else:
            w = self._default_width * self.sprite_model.size
            h = self._default_height * self.sprite_model.size

        # Apply rotation
        painter.save()
        painter.rotate(90 - self.sprite_model.direction)

        # Draw the sprite
        if self._pixmap and not self._pixmap.isNull():
            # Draw scaled pixmap
            scaled = self._pixmap.scaled(
                int(w), int(h),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(
                int(-scaled.width() / 2),
                int(-scaled.height() / 2),
                scaled
            )
        else:
            # Draw placeholder rectangle
            rect = QRectF(-w/2, -h/2, w, h)
            painter.setPen(QPen(QColor(100, 100, 100), 2))
            painter.setBrush(QBrush(QColor(200, 200, 200, 150)))
            painter.drawRect(rect)

            # Draw sprite name
            painter.setPen(QColor(50, 50, 50))
            painter.drawText(rect, Qt.AlignCenter, self.sprite_model.name)

        painter.restore()

        # Draw selection handles
        if self.isSelected():
            self._draw_selection_handles(painter, w, h)

    def _draw_selection_handles(self, painter: QPainter, w: float, h: float):
        """Draw selection handles around the sprite."""
        painter.setPen(QPen(QColor(0, 120, 215), 2))
        painter.setBrush(Qt.NoBrush)

        # Selection rectangle
        rect = QRectF(-w/2, -h/2, w, h)
        painter.drawRect(rect)

        # Corner handles
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        handle_positions = [
            (-w/2, -h/2),  # Top-left
            (w/2, -h/2),   # Top-right
            (-w/2, h/2),   # Bottom-left
            (w/2, h/2),    # Bottom-right
        ]

        for x, y in handle_positions:
            painter.drawRect(
                x - self.HANDLE_HALF,
                y - self.HANDLE_HALF,
                self.HANDLE_SIZE,
                self.HANDLE_SIZE
            )

        # Direction indicator
        painter.setPen(QPen(QColor(255, 100, 100), 2))
        painter.drawLine(0, 0, int(w/3), 0)

    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update model position
            pos = self.pos()
            self.sprite_model.x = pos.x()
            self.sprite_model.y = pos.y()

        return super().itemChange(change, value)

    def update_from_model(self):
        """Update the item from its model."""
        self.setPos(self.sprite_model.x, self.sprite_model.y)
        self._load_costume()
        self.update()

    def set_costume(self, path: str):
        """Set the sprite's costume."""
        if os.path.exists(path):
            self._pixmap = QPixmap(path)
            if path not in self.sprite_model.costumes:
                self.sprite_model.costumes.append(path)
            self.sprite_model.current_costume = self.sprite_model.costumes.index(path)
            self.prepareGeometryChange()
            self.update()


class GridBackground(QGraphicsRectItem):
    """Background grid for the scene editor."""

    def __init__(self, width: int, height: int, grid_size: int = 32, parent=None):
        super().__init__(0, 0, width, height, parent)

        self.grid_size = grid_size
        self.setZValue(-1000)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the grid background."""
        rect = self.rect()

        # Background color
        painter.fillRect(rect, QColor(40, 40, 40))

        # Grid lines
        painter.setPen(QPen(QColor(60, 60, 60), 1))

        # Vertical lines
        x = 0
        while x <= rect.width():
            painter.drawLine(int(x), 0, int(x), int(rect.height()))
            x += self.grid_size

        # Horizontal lines
        y = 0
        while y <= rect.height():
            painter.drawLine(0, int(y), int(rect.width()), int(y))
            y += self.grid_size

        # Origin crosshair
        cx, cy = rect.width() / 2, rect.height() / 2
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawLine(int(cx - 20), int(cy), int(cx + 20), int(cy))
        painter.drawLine(int(cx), int(cy - 20), int(cx), int(cy + 20))

        # Border
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawRect(rect)
