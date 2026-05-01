"""
Navigation Grid Editor

Visual editor for painting walkable/blocked cells on a navigation grid.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QSpinBox, QToolButton, QButtonGroup, QFormLayout,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QMouseEvent, QPaintEvent
)
from typing import Optional, Dict, List, Tuple, Set


class NavGridCanvas(QWidget):
    """Canvas for painting navigation grid obstacles."""

    grid_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._width = 20
        self._height = 15
        self._cell_size = 24
        self._obstacles: Set[Tuple[int, int]] = set()
        self._weights: Dict[Tuple[int, int], float] = {}
        self._painting = False
        self._tool = "obstacle"  # obstacle, weight, erase
        self._paint_value = True  # True = add, False = remove
        self.setMinimumSize(
            self._width * self._cell_size,
            self._height * self._cell_size
        )

    def set_grid_size(self, w: int, h: int):
        self._width = w
        self._height = h
        self.setMinimumSize(w * self._cell_size, h * self._cell_size)
        # Remove out-of-bounds obstacles
        self._obstacles = {
            (x, y) for x, y in self._obstacles
            if 0 <= x < w and 0 <= y < h
        }
        self.update()

    def set_tool(self, tool: str):
        self._tool = tool

    def get_obstacles(self) -> List[Tuple[int, int]]:
        return list(self._obstacles)

    def set_obstacles(self, obstacles: List[Tuple[int, int]]):
        self._obstacles = set(tuple(o) for o in obstacles)
        self.update()

    def clear(self):
        self._obstacles.clear()
        self._weights.clear()
        self.grid_changed.emit()
        self.update()

    def to_string(self) -> str:
        """Serialize: rows of 0/1 (0=walkable, 1=obstacle)."""
        lines = []
        for y in range(self._height):
            row = []
            for x in range(self._width):
                row.append("1" if (x, y) in self._obstacles else "0")
            lines.append(",".join(row))
        return "\n".join(lines)

    def from_string(self, data: str):
        if not data.strip():
            return
        self._obstacles.clear()
        for y, line in enumerate(data.strip().split("\n")):
            for x, val in enumerate(line.split(",")):
                if val.strip() == "1":
                    self._obstacles.add((x, y))
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        cs = self._cell_size

        # Background (walkable)
        painter.fillRect(self.rect(), QColor(40, 60, 40))

        # Obstacles
        for (x, y) in self._obstacles:
            if 0 <= x < self._width and 0 <= y < self._height:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(80, 30, 30)))
                painter.drawRect(x * cs, y * cs, cs, cs)

                # X mark
                painter.setPen(QPen(QColor(200, 80, 80), 2))
                margin = 4
                painter.drawLine(
                    x * cs + margin, y * cs + margin,
                    (x + 1) * cs - margin, (y + 1) * cs - margin
                )
                painter.drawLine(
                    (x + 1) * cs - margin, y * cs + margin,
                    x * cs + margin, (y + 1) * cs - margin
                )

        # Grid
        painter.setPen(QPen(QColor(60, 80, 60), 1))
        for x in range(self._width + 1):
            painter.drawLine(x * cs, 0, x * cs, self._height * cs)
        for y in range(self._height + 1):
            painter.drawLine(0, y * cs, self._width * cs, y * cs)

        # Border
        painter.setPen(QPen(QColor(100, 130, 100), 2))
        painter.drawRect(0, 0, self._width * cs, self._height * cs)

        # Legend
        painter.setPen(QColor(150, 150, 150))
        bottom_y = self._height * cs + 15
        if bottom_y < self.height():
            painter.drawText(10, bottom_y, "🟩 可通行  🟥 障碍物")

        painter.end()

    def _cell_at(self, pos) -> Optional[Tuple[int, int]]:
        x = int(pos.x()) // self._cell_size
        y = int(pos.y()) // self._cell_size
        if 0 <= x < self._width and 0 <= y < self._height:
            return (x, y)
        return None

    def _paint_cell(self, cell: Tuple[int, int]):
        if self._tool == "erase":
            self._obstacles.discard(cell)
        elif self._tool == "obstacle":
            if self._paint_value:
                self._obstacles.add(cell)
            else:
                self._obstacles.discard(cell)
        self.grid_changed.emit()
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._painting = True
            cell = self._cell_at(event.position())
            if cell:
                # Toggle behavior: if clicking on obstacle, erase; else add
                if cell in self._obstacles:
                    self._paint_value = False
                else:
                    self._paint_value = True
                self._paint_cell(cell)
        elif event.button() == Qt.RightButton:
            cell = self._cell_at(event.position())
            if cell:
                self._obstacles.discard(cell)
                self.grid_changed.emit()
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._painting:
            cell = self._cell_at(event.position())
            if cell:
                self._paint_cell(cell)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._painting = False


class NavigationGridEditor(QWidget):
    """Complete Navigation Grid editor."""

    data_changed = Signal(str)  # serialized grid data

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Grid size
        size_group = QGroupBox("网格设置")
        sg_layout = QFormLayout(size_group)

        self._grid_w = QSpinBox()
        self._grid_w.setRange(2, 100)
        self._grid_w.setValue(20)
        self._grid_w.valueChanged.connect(self._on_size_changed)
        sg_layout.addRow("宽度:", self._grid_w)

        self._grid_h = QSpinBox()
        self._grid_h.setRange(2, 100)
        self._grid_h.setValue(15)
        self._grid_h.valueChanged.connect(self._on_size_changed)
        sg_layout.addRow("高度:", self._grid_h)

        layout.addWidget(size_group)

        # Tools
        tools_row = QHBoxLayout()

        self._tool_group = QButtonGroup(self)
        self._tool_group.setExclusive(True)

        obstacle_btn = QToolButton()
        obstacle_btn.setText("🧱 绘制障碍")
        obstacle_btn.setCheckable(True)
        obstacle_btn.setChecked(True)
        self._tool_group.addButton(obstacle_btn)
        obstacle_btn.clicked.connect(lambda: self._canvas.set_tool("obstacle"))
        tools_row.addWidget(obstacle_btn)

        erase_btn = QToolButton()
        erase_btn.setText("🧹 擦除")
        erase_btn.setCheckable(True)
        self._tool_group.addButton(erase_btn)
        erase_btn.clicked.connect(lambda: self._canvas.set_tool("erase"))
        tools_row.addWidget(erase_btn)

        tools_row.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._clear)
        tools_row.addWidget(clear_btn)

        layout.addLayout(tools_row)

        # Canvas
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        self._canvas = NavGridCanvas()
        self._canvas.grid_changed.connect(self._on_grid_changed)
        scroll.setWidget(self._canvas)
        layout.addWidget(scroll, 1)

        # Stats
        self._stats_label = QLabel("障碍物: 0")
        layout.addWidget(self._stats_label)

    def _on_size_changed(self):
        self._canvas.set_grid_size(self._grid_w.value(), self._grid_h.value())

    def _clear(self):
        self._canvas.clear()
        self._update_stats()
        self._on_grid_changed()

    def _on_grid_changed(self):
        self._update_stats()
        self.data_changed.emit(self._canvas.to_string())

    def _update_stats(self):
        total = self._grid_w.value() * self._grid_h.value()
        obstacles = len(self._canvas.get_obstacles())
        self._stats_label.setText(
            f"障碍物: {obstacles} / {total} 格 "
            f"({obstacles * 100 // total}%)" if total > 0 else ""
        )

    # --- Public API ---

    def load_data(self, data_str: str, width: int = 20, height: int = 15):
        self._grid_w.setValue(width)
        self._grid_h.setValue(height)
        self._canvas.set_grid_size(width, height)
        if data_str:
            self._canvas.from_string(data_str)
        self._update_stats()

    def get_data(self) -> str:
        return self._canvas.to_string()
