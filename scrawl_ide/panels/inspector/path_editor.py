"""
Path2D Point Editor

Visual editor for creating and editing path points.
Supports click-to-add, drag, and delete operations.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QCheckBox, QDoubleSpinBox, QFormLayout,
    QListWidget, QListWidgetItem, QColorDialog
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QMouseEvent, QPaintEvent,
    QPainterPath
)
from typing import Optional, List, Tuple


class PathCanvas(QWidget):
    """Canvas for visual path point editing."""

    points_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._points: List[Tuple[float, float]] = []
        self._closed = False
        self._line_color = QColor(200, 100, 200)
        self._line_width = 2.0
        self._selected_point = -1
        self._dragging = False
        self._drag_offset = QPointF(0, 0)
        self._canvas_offset = QPointF(200, 150)  # Center offset
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

    @property
    def points(self) -> List[Tuple[float, float]]:
        return list(self._points)

    @points.setter
    def points(self, pts: List[Tuple[float, float]]):
        self._points = list(pts)
        self.update()

    @property
    def closed(self) -> bool:
        return self._closed

    @closed.setter
    def closed(self, v: bool):
        self._closed = v
        self.update()

    def set_line_color(self, color: QColor):
        self._line_color = color
        self.update()

    def set_line_width(self, w: float):
        self._line_width = w
        self.update()

    def _world_to_screen(self, x: float, y: float) -> QPointF:
        return QPointF(x + self._canvas_offset.x(), y + self._canvas_offset.y())

    def _screen_to_world(self, pos: QPointF) -> Tuple[float, float]:
        return (pos.x() - self._canvas_offset.x(),
                pos.y() - self._canvas_offset.y())

    def _point_at(self, pos: QPointF) -> int:
        """Find point index near screen position."""
        for i, (px, py) in enumerate(self._points):
            sp = self._world_to_screen(px, py)
            if (sp - pos).manhattanLength() < 12:
                return i
        return -1

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(35, 35, 40))

        # Grid
        painter.setPen(QPen(QColor(50, 50, 55), 1))
        ox, oy = int(self._canvas_offset.x()), int(self._canvas_offset.y())
        for x in range(0, self.width(), 32):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 32):
            painter.drawLine(0, y, self.width(), y)

        # Origin crosshair
        painter.setPen(QPen(QColor(80, 80, 90), 1))
        painter.drawLine(ox - 20, oy, ox + 20, oy)
        painter.drawLine(ox, oy - 20, ox, oy + 20)

        # Draw path
        if len(self._points) >= 2:
            painter.setPen(QPen(self._line_color, self._line_width))
            path = QPainterPath()
            sp0 = self._world_to_screen(*self._points[0])
            path.moveTo(sp0)
            for px, py in self._points[1:]:
                sp = self._world_to_screen(px, py)
                path.lineTo(sp)
            if self._closed and len(self._points) >= 3:
                path.closeSubpath()
            painter.drawPath(path)

        # Draw points
        for i, (px, py) in enumerate(self._points):
            sp = self._world_to_screen(px, py)
            if i == self._selected_point:
                painter.setPen(QPen(QColor(0, 200, 255), 2))
                painter.setBrush(QBrush(QColor(0, 200, 255, 180)))
            else:
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.setBrush(QBrush(QColor(200, 100, 200, 180)))
            painter.drawEllipse(sp, 6, 6)

            # Point index
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(sp.x() + 8, sp.y() - 8, str(i))

        # Instructions
        painter.setPen(QColor(100, 100, 100))
        painter.drawText(10, self.height() - 10,
                         "左键添加点 | 拖拽移动点 | 右键删除点")

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()

        if event.button() == Qt.LeftButton:
            idx = self._point_at(pos)
            if idx >= 0:
                # Start dragging
                self._selected_point = idx
                self._dragging = True
                sp = self._world_to_screen(*self._points[idx])
                self._drag_offset = sp - pos
            else:
                # Add new point
                wx, wy = self._screen_to_world(pos)
                self._points.append((round(wx, 1), round(wy, 1)))
                self._selected_point = len(self._points) - 1
                self.points_changed.emit()
            self.update()

        elif event.button() == Qt.RightButton:
            idx = self._point_at(pos)
            if idx >= 0:
                self._points.pop(idx)
                self._selected_point = -1
                self.points_changed.emit()
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self._selected_point >= 0:
            pos = event.position() + self._drag_offset
            wx, wy = self._screen_to_world(pos)
            self._points[self._selected_point] = (round(wx, 1), round(wy, 1))
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self.points_changed.emit()


class PathEditor(QWidget):
    """Complete Path2D/Line2D editor."""

    data_changed = Signal(list, bool, float, tuple)  # points, loop, width, color

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Settings
        settings_group = QGroupBox("路径设置")
        sg_layout = QFormLayout(settings_group)

        self._loop_check = QCheckBox()
        self._loop_check.toggled.connect(self._on_setting_changed)
        sg_layout.addRow("闭合路径:", self._loop_check)

        self._width_spin = QDoubleSpinBox()
        self._width_spin.setRange(0.5, 20.0)
        self._width_spin.setValue(2.0)
        self._width_spin.setSingleStep(0.5)
        self._width_spin.valueChanged.connect(self._on_width_changed)
        sg_layout.addRow("线宽:", self._width_spin)

        color_row = QHBoxLayout()
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(60, 24)
        self._line_color = (200, 100, 200)
        self._update_color_btn()
        self._color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self._color_btn)
        sg_layout.addRow("线颜色:", color_row)

        layout.addWidget(settings_group)

        # Canvas
        self._canvas = PathCanvas()
        self._canvas.points_changed.connect(self._on_points_changed)
        layout.addWidget(self._canvas, 1)

        # Point list
        points_group = QGroupBox("点列表")
        pg_layout = QVBoxLayout(points_group)

        self._point_list = QListWidget()
        self._point_list.setMaximumHeight(100)
        pg_layout.addWidget(self._point_list)

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("清空所有点")
        clear_btn.clicked.connect(self._clear_points)
        btn_row.addWidget(clear_btn)
        pg_layout.addLayout(btn_row)

        layout.addWidget(points_group)

    def _update_color_btn(self):
        r, g, b = self._line_color
        self._color_btn.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border: 1px solid #555;"
        )

    def _pick_color(self):
        r, g, b = self._line_color
        color = QColorDialog.getColor(QColor(r, g, b), self, "线颜色")
        if color.isValid():
            self._line_color = (color.red(), color.green(), color.blue())
            self._update_color_btn()
            self._canvas.set_line_color(color)
            self._emit_change()

    def _on_width_changed(self, value: float):
        self._canvas.set_line_width(value)
        self._emit_change()

    def _on_setting_changed(self):
        self._canvas.closed = self._loop_check.isChecked()
        self._emit_change()

    def _on_points_changed(self):
        self._refresh_point_list()
        self._emit_change()

    def _refresh_point_list(self):
        self._point_list.clear()
        for i, (x, y) in enumerate(self._canvas.points):
            self._point_list.addItem(f"点 {i}: ({x}, {y})")

    def _clear_points(self):
        self._canvas.points = []
        self._canvas.points_changed.emit()
        self._canvas.update()

    def _emit_change(self):
        self.data_changed.emit(
            self._canvas.points,
            self._loop_check.isChecked(),
            self._width_spin.value(),
            self._line_color
        )

    # --- Public API ---

    def load_data(self, points: List, loop: bool, width: float,
                  color: Tuple[int, int, int]):
        self._canvas.points = [(float(p[0]), float(p[1])) for p in points] if points else []
        self._loop_check.setChecked(loop)
        self._width_spin.setValue(width)
        self._line_color = color
        self._update_color_btn()
        self._canvas.closed = loop
        self._canvas.set_line_color(QColor(color[0], color[1], color[2]))
        self._canvas.set_line_width(width)
        self._refresh_point_list()

    def get_points(self) -> List[Tuple[float, float]]:
        return self._canvas.points
