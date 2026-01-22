"""
Scene View

QGraphicsView-based scene editor with zoom, pan, and selection support.
"""

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QRubberBand
)
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QRectF
from PySide6.QtGui import (
    QPainter, QWheelEvent, QMouseEvent, QKeyEvent,
    QColor, QTransform
)
from typing import Optional, Dict

from models import SpriteModel
from .scene_items import SpriteItem, GridBackground


class SceneView(QGraphicsView):
    """Scene editor view with zoom and pan support."""

    sprite_selected = Signal(object)  # SpriteModel
    sprite_moved = Signal(object, float, float)  # SpriteModel, x, y
    sprite_added = Signal(object)  # SpriteModel
    selection_cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._sprite_items: Dict[str, SpriteItem] = {}
        self._grid: Optional[GridBackground] = None
        self._selected_item: Optional[SpriteItem] = None

        # View settings
        self._zoom_factor = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 5.0

        # Tool state
        self._current_tool = "select"  # "select" or "pan"
        self._snap_enabled = False
        self._grid_size = 32

        # Pan state
        self._panning = False
        self._pan_start = QPoint()

        # Scene size (default game size)
        self._scene_width = 800
        self._scene_height = 600

        self._setup_view()
        self._setup_scene()

    def _setup_view(self):
        """Configure the view."""
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # Enable drops
        self.setAcceptDrops(True)

    def _setup_scene(self):
        """Set up the scene with grid background."""
        # Set scene rect with some margin
        margin = 200
        self._scene.setSceneRect(
            -margin, -margin,
            self._scene_width + margin * 2,
            self._scene_height + margin * 2
        )

        # Add grid background
        self._grid = GridBackground(self._scene_width, self._scene_height)
        self._scene.addItem(self._grid)

        # Center the view
        self.centerOn(self._scene_width / 2, self._scene_height / 2)

    def set_scene_size(self, width: int, height: int):
        """Set the scene size."""
        self._scene_width = width
        self._scene_height = height

        # Remove old grid
        if self._grid:
            self._scene.removeItem(self._grid)

        # Set new scene rect
        margin = 200
        self._scene.setSceneRect(
            -margin, -margin,
            width + margin * 2,
            height + margin * 2
        )

        # Add new grid
        self._grid = GridBackground(width, height)
        self._scene.addItem(self._grid)

    def clear(self):
        """Clear all sprites from the scene."""
        for item in list(self._sprite_items.values()):
            self._scene.removeItem(item)
        self._sprite_items.clear()
        self._selected_item = None

    def add_sprite(self, sprite: SpriteModel) -> SpriteItem:
        """Add a sprite to the scene."""
        item = SpriteItem(sprite)
        self._scene.addItem(item)
        self._sprite_items[sprite.id] = item
        return item

    def remove_sprite(self, sprite_id: str):
        """Remove a sprite from the scene."""
        if sprite_id in self._sprite_items:
            item = self._sprite_items.pop(sprite_id)
            self._scene.removeItem(item)
            if self._selected_item == item:
                self._selected_item = None

    def select_sprite(self, sprite: SpriteModel):
        """Select a sprite by model."""
        # Clear current selection
        self._scene.clearSelection()

        if sprite and sprite.id in self._sprite_items:
            item = self._sprite_items[sprite.id]
            item.setSelected(True)
            self._selected_item = item
            self.centerOn(item)

    def update_sprite(self, sprite: SpriteModel):
        """Update a sprite item from its model."""
        if sprite.id in self._sprite_items:
            item = self._sprite_items[sprite.id]
            item.update_from_model()

    def get_selected_sprite(self) -> Optional[SpriteModel]:
        """Get the currently selected sprite model."""
        selected = self._scene.selectedItems()
        if selected and isinstance(selected[0], SpriteItem):
            return selected[0].sprite_model
        return None

    # Zoom methods
    def zoom_in(self):
        """Zoom in."""
        self._apply_zoom(1.25)

    def zoom_out(self):
        """Zoom out."""
        self._apply_zoom(0.8)

    def zoom_reset(self):
        """Reset zoom to 100%."""
        self.resetTransform()
        self._zoom_factor = 1.0

    def zoom_fit(self):
        """Fit the scene in the view."""
        self.fitInView(
            QRectF(0, 0, self._scene_width, self._scene_height),
            Qt.KeepAspectRatio
        )
        self._zoom_factor = self.transform().m11()

    def _apply_zoom(self, factor: float):
        """Apply zoom factor."""
        new_zoom = self._zoom_factor * factor

        if self._min_zoom <= new_zoom <= self._max_zoom:
            self._zoom_factor = new_zoom
            self.scale(factor, factor)

    def set_zoom(self, factor: float):
        """Set absolute zoom level."""
        if self._min_zoom <= factor <= self._max_zoom:
            # Reset and apply new zoom
            self.resetTransform()
            self._zoom_factor = factor
            self.scale(factor, factor)

    def get_zoom(self) -> float:
        """Get current zoom factor."""
        return self._zoom_factor

    def set_tool(self, tool: str):
        """Set the current tool (select or pan)."""
        self._current_tool = tool
        if tool == "pan":
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        else:  # select
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)

    def set_grid_visible(self, visible: bool):
        """Show or hide the grid."""
        if self._grid:
            self._grid.setVisible(visible)

    def set_snap_enabled(self, enabled: bool):
        """Enable or disable snap to grid."""
        self._snap_enabled = enabled

    def set_grid_size(self, size: int):
        """Set the grid size for snapping."""
        self._grid_size = size
        if self._grid:
            self._grid.grid_size = size
            self._grid.update()

    def _snap_to_grid(self, pos: QPoint) -> QPoint:
        """Snap a position to the grid."""
        if not self._snap_enabled:
            return pos
        x = round(pos.x() / self._grid_size) * self._grid_size
        y = round(pos.y() / self._grid_size) * self._grid_size
        return QPoint(int(x), int(y))

    # Event handlers
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom with Ctrl + wheel
            delta = event.angleDelta().y()
            if delta > 0:
                self._apply_zoom(1.1)
            else:
                self._apply_zoom(0.9)
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and self._current_tool == "pan"
        ):
            # Start panning
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

            # Check for selection change
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, SpriteItem):
                if item != self._selected_item:
                    self._selected_item = item
                    self.sprite_selected.emit(item.sprite_model)
            elif item is None or item == self._grid:
                if self._selected_item:
                    self._selected_item = None
                    self.selection_cleared.emit()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move."""
        if self._panning:
            # Pan the view
            delta = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        if (event.button() == Qt.MiddleButton or
            (event.button() == Qt.LeftButton and self._current_tool == "pan")) and self._panning:
            self._panning = False
            if self._current_tool == "pan":
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

            # Emit move signal if item was moved and apply snap
            if self._selected_item:
                model = self._selected_item.sprite_model
                pos = self._selected_item.pos()

                # Apply snap to grid if enabled
                if self._snap_enabled:
                    snapped_x = round(pos.x() / self._grid_size) * self._grid_size
                    snapped_y = round(pos.y() / self._grid_size) * self._grid_size
                    self._selected_item.setPos(snapped_x, snapped_y)
                    pos = self._selected_item.pos()

                if model.x != pos.x() or model.y != pos.y():
                    self.sprite_moved.emit(model, pos.x(), pos.y())

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press."""
        if event.key() == Qt.Key_Delete:
            # Delete selected sprite
            if self._selected_item:
                sprite_id = self._selected_item.sprite_model.id
                self.remove_sprite(sprite_id)
        elif event.key() == Qt.Key_Escape:
            # Clear selection
            self._scene.clearSelection()
            self._selected_item = None
            self.selection_cleared.emit()
        else:
            super().keyPressEvent(event)

    # Drag and drop
    def dragEnterEvent(self, event):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Handle drag move."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                path = url.toLocalFile()
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')):
                    # Create new sprite with this image
                    import os
                    name = os.path.splitext(os.path.basename(path))[0]
                    sprite = SpriteModel.create_default(name)

                    # Set position to drop location
                    scene_pos = self.mapToScene(event.position().toPoint())
                    sprite.x = scene_pos.x()
                    sprite.y = scene_pos.y()
                    # Use add_costume method for new CostumeData format
                    sprite.add_costume(name, path)

                    # Add to scene
                    self.add_sprite(sprite)
                    self.sprite_added.emit(sprite)

            event.acceptProposedAction()
