"""
TileMap Editor

Visual tile painting tool for TileMap nodes.
Supports defining tilesets and painting tiles on a grid.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSpinBox, QScrollArea,
    QGroupBox, QColorDialog, QInputDialog, QListWidget,
    QListWidgetItem, QToolButton, QButtonGroup, QComboBox,
    QMenu, QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QMouseEvent, QPaintEvent,
    QAction
)
from typing import Optional, Dict, List, Tuple


class TilePalette(QWidget):
    """Tile palette for selecting tiles to paint."""

    tile_selected = Signal(int)  # tile_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tiles: Dict[int, dict] = {}  # id -> {name, color, collision}
        self._selected_id = -1
        self._cell_size = 32
        self._cols = 4
        self.setMinimumHeight(100)

    def set_tiles(self, tiles: Dict[int, dict]):
        self._tiles = tiles
        self.update()

    def add_tile(self, tile_id: int, name: str, color: Tuple[int, int, int],
                 collision: bool = False):
        self._tiles[tile_id] = {
            "name": name, "color": color, "collision": collision
        }
        self.update()

    def remove_tile(self, tile_id: int):
        self._tiles.pop(tile_id, None)
        if self._selected_id == tile_id:
            self._selected_id = -1
        self.update()

    @property
    def selected_tile(self) -> int:
        return self._selected_id

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cs = self._cell_size
        sorted_ids = sorted(self._tiles.keys())

        # Eraser tile at position 0
        ex, ey = 0, 0
        rect = QRect(ex * cs + 2, ey * cs + 2, cs - 4, cs - 4)
        painter.setPen(QPen(QColor(200, 50, 50), 2))
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawRect(rect)
        painter.setPen(QColor(200, 50, 50))
        painter.drawText(rect, Qt.AlignCenter, "✕")
        if self._selected_id == -1:
            painter.setPen(QPen(QColor(0, 150, 255), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect.adjusted(-2, -2, 2, 2))

        for i, tid in enumerate(sorted_ids):
            tile = self._tiles[tid]
            col = (i + 1) % self._cols
            row = (i + 1) // self._cols

            x = col * cs + 2
            y = row * cs + 2
            rect = QRect(x, y, cs - 4, cs - 4)

            c = tile["color"]
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.setBrush(QBrush(QColor(c[0], c[1], c[2])))
            painter.drawRect(rect)

            # Collision indicator
            if tile.get("collision"):
                painter.setPen(QPen(QColor(255, 100, 100), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect.adjusted(2, 2, -2, -2))

            # Name
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(rect, Qt.AlignCenter, str(tid))

            # Selection highlight
            if tid == self._selected_id:
                painter.setPen(QPen(QColor(0, 150, 255), 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect.adjusted(-2, -2, 2, 2))

        rows_needed = ((len(sorted_ids) + 1) // self._cols) + 1
        self.setMinimumHeight(rows_needed * cs + 4)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        cs = self._cell_size
        col = int(event.position().x()) // cs
        row = int(event.position().y()) // cs
        idx = row * self._cols + col

        if idx == 0:
            self._selected_id = -1
            self.tile_selected.emit(-1)
        else:
            sorted_ids = sorted(self._tiles.keys())
            real_idx = idx - 1
            if 0 <= real_idx < len(sorted_ids):
                self._selected_id = sorted_ids[real_idx]
                self.tile_selected.emit(self._selected_id)

        self.update()


class TileMapCanvas(QWidget):
    """Canvas for painting tiles on a grid."""

    map_changed = Signal()  # emitted when tiles change

    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid_width = 20
        self._grid_height = 15
        self._cell_size = 24
        self._cells: Dict[Tuple[int, int], int] = {}
        self._tile_colors: Dict[int, Tuple[int, int, int]] = {}
        self._current_tile = -1
        self._painting = False
        self._tool = "paint"  # paint, erase, fill
        self.setMinimumSize(
            self._grid_width * self._cell_size,
            self._grid_height * self._cell_size
        )

    def set_grid_size(self, w: int, h: int):
        self._grid_width = w
        self._grid_height = h
        self.setMinimumSize(w * self._cell_size, h * self._cell_size)
        self.update()

    def set_current_tile(self, tile_id: int):
        self._current_tile = tile_id

    def set_tool(self, tool: str):
        self._tool = tool

    def set_tile_colors(self, colors: Dict[int, Tuple[int, int, int]]):
        self._tile_colors = colors
        self.update()

    def get_cells(self) -> Dict[Tuple[int, int], int]:
        return dict(self._cells)

    def set_cells(self, cells: Dict[Tuple[int, int], int]):
        self._cells = dict(cells)
        self.update()

    def clear(self):
        self._cells.clear()
        self.map_changed.emit()
        self.update()

    def to_array(self) -> List[List[int]]:
        """Export as 2D array."""
        result = []
        for y in range(self._grid_height):
            row = []
            for x in range(self._grid_width):
                row.append(self._cells.get((x, y), -1))
            result.append(row)
        return result

    def from_array(self, data: List[List[int]]):
        """Import from 2D array."""
        self._cells.clear()
        for y, row in enumerate(data):
            for x, tid in enumerate(row):
                if tid >= 0:
                    self._cells[(x, y)] = tid
        self.update()

    def to_string(self) -> str:
        """Export as string for serialization."""
        arr = self.to_array()
        lines = []
        for row in arr:
            lines.append(",".join(str(v) for v in row))
        return "\n".join(lines)

    def from_string(self, data: str):
        """Import from serialized string."""
        if not data.strip():
            return
        self._cells.clear()
        for y, line in enumerate(data.strip().split("\n")):
            for x, val in enumerate(line.split(",")):
                tid = int(val.strip())
                if tid >= 0:
                    self._cells[(x, y)] = tid
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        cs = self._cell_size

        # Background
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        # Draw cells
        for (x, y), tid in self._cells.items():
            if 0 <= x < self._grid_width and 0 <= y < self._grid_height:
                color = self._tile_colors.get(tid, (128, 128, 128))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(color[0], color[1], color[2])))
                painter.drawRect(x * cs, y * cs, cs, cs)
                # Tile ID text
                painter.setPen(QColor(255, 255, 255, 120))
                painter.drawText(
                    QRect(x * cs, y * cs, cs, cs),
                    Qt.AlignCenter, str(tid)
                )

        # Grid lines
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        for x in range(self._grid_width + 1):
            painter.drawLine(x * cs, 0, x * cs, self._grid_height * cs)
        for y in range(self._grid_height + 1):
            painter.drawLine(0, y * cs, self._grid_width * cs, y * cs)

        # Border
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(0, 0, self._grid_width * cs, self._grid_height * cs)

        painter.end()

    def _cell_at(self, pos) -> Optional[Tuple[int, int]]:
        x = int(pos.x()) // self._cell_size
        y = int(pos.y()) // self._cell_size
        if 0 <= x < self._grid_width and 0 <= y < self._grid_height:
            return (x, y)
        return None

    def _paint_cell(self, cell: Tuple[int, int]):
        if self._tool == "erase" or self._current_tile < 0:
            self._cells.pop(cell, None)
        elif self._tool == "fill":
            self._flood_fill(cell, self._current_tile)
        else:
            self._cells[cell] = self._current_tile
        self.map_changed.emit()
        self.update()

    def _flood_fill(self, start: Tuple[int, int], tile_id: int):
        target = self._cells.get(start, -1)
        if target == tile_id:
            return
        stack = [start]
        visited = set()
        while stack:
            pos = stack.pop()
            if pos in visited:
                continue
            visited.add(pos)
            x, y = pos
            if x < 0 or x >= self._grid_width or y < 0 or y >= self._grid_height:
                continue
            current = self._cells.get(pos, -1)
            if current != target:
                continue
            if tile_id >= 0:
                self._cells[pos] = tile_id
            else:
                self._cells.pop(pos, None)
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._painting = True
            cell = self._cell_at(event.position())
            if cell:
                self._paint_cell(cell)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._painting:
            cell = self._cell_at(event.position())
            if cell:
                self._paint_cell(cell)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._painting = False


class TileMapEditor(QWidget):
    """Complete TileMap editor with palette and canvas."""

    data_changed = Signal(str)  # serialized tilemap data

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tiles: Dict[int, dict] = {}
        self._next_id = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # --- Tileset management ---
        tileset_group = QGroupBox("瓦片集")
        tg_layout = QVBoxLayout(tileset_group)

        # Tile palette
        self._palette = TilePalette()
        self._palette.tile_selected.connect(self._on_tile_selected)
        tg_layout.addWidget(self._palette)

        # Tile management buttons
        btn_row = QHBoxLayout()
        add_btn = QPushButton("添加瓦片")
        add_btn.clicked.connect(self._add_tile)
        btn_row.addWidget(add_btn)

        remove_btn = QPushButton("删除瓦片")
        remove_btn.clicked.connect(self._remove_tile)
        btn_row.addWidget(remove_btn)

        edit_btn = QPushButton("编辑颜色")
        edit_btn.clicked.connect(self._edit_tile_color)
        btn_row.addWidget(edit_btn)

        collision_btn = QPushButton("切换碰撞")
        collision_btn.clicked.connect(self._toggle_collision)
        btn_row.addWidget(collision_btn)

        tg_layout.addLayout(btn_row)
        layout.addWidget(tileset_group)

        # --- Tools ---
        tools_layout = QHBoxLayout()

        self._tool_group = QButtonGroup(self)
        self._tool_group.setExclusive(True)

        paint_btn = QToolButton()
        paint_btn.setText("🖌️ 绘制")
        paint_btn.setCheckable(True)
        paint_btn.setChecked(True)
        self._tool_group.addButton(paint_btn)
        paint_btn.clicked.connect(lambda: self._canvas.set_tool("paint"))
        tools_layout.addWidget(paint_btn)

        erase_btn = QToolButton()
        erase_btn.setText("🧹 擦除")
        erase_btn.setCheckable(True)
        self._tool_group.addButton(erase_btn)
        erase_btn.clicked.connect(lambda: self._canvas.set_tool("erase"))
        tools_layout.addWidget(erase_btn)

        fill_btn = QToolButton()
        fill_btn.setText("🪣 填充")
        fill_btn.setCheckable(True)
        self._tool_group.addButton(fill_btn)
        fill_btn.clicked.connect(lambda: self._canvas.set_tool("fill"))
        tools_layout.addWidget(fill_btn)

        tools_layout.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._clear_map)
        tools_layout.addWidget(clear_btn)

        layout.addLayout(tools_layout)

        # --- Grid size ---
        grid_row = QHBoxLayout()
        grid_row.addWidget(QLabel("宽:"))
        self._grid_w_spin = QSpinBox()
        self._grid_w_spin.setRange(2, 100)
        self._grid_w_spin.setValue(20)
        self._grid_w_spin.valueChanged.connect(self._on_grid_size_changed)
        grid_row.addWidget(self._grid_w_spin)

        grid_row.addWidget(QLabel("高:"))
        self._grid_h_spin = QSpinBox()
        self._grid_h_spin.setRange(2, 100)
        self._grid_h_spin.setValue(15)
        self._grid_h_spin.valueChanged.connect(self._on_grid_size_changed)
        grid_row.addWidget(self._grid_h_spin)
        layout.addLayout(grid_row)

        # --- Canvas ---
        canvas_scroll = QScrollArea()
        canvas_scroll.setWidgetResizable(False)
        self._canvas = TileMapCanvas()
        self._canvas.map_changed.connect(self._on_map_changed)
        canvas_scroll.setWidget(self._canvas)
        layout.addWidget(canvas_scroll, 1)

    def _on_tile_selected(self, tile_id: int):
        self._canvas.set_current_tile(tile_id)

    def _add_tile(self):
        name, ok = QInputDialog.getText(self, "添加瓦片", "瓦片名称:",
                                        text=f"tile_{self._next_id}")
        if not ok or not name:
            return

        color = QColorDialog.getColor(QColor(128, 128, 128), self, "瓦片颜色")
        if not color.isValid():
            return

        tid = self._next_id
        self._next_id += 1
        c = (color.red(), color.green(), color.blue())
        self._tiles[tid] = {"name": name, "color": c, "collision": False}
        self._palette.add_tile(tid, name, c)
        self._update_canvas_colors()

    def _remove_tile(self):
        tid = self._palette.selected_tile
        if tid < 0:
            return
        self._tiles.pop(tid, None)
        self._palette.remove_tile(tid)
        self._update_canvas_colors()

    def _edit_tile_color(self):
        tid = self._palette.selected_tile
        if tid < 0 or tid not in self._tiles:
            return
        old_c = self._tiles[tid]["color"]
        color = QColorDialog.getColor(
            QColor(old_c[0], old_c[1], old_c[2]), self, "瓦片颜色"
        )
        if color.isValid():
            c = (color.red(), color.green(), color.blue())
            self._tiles[tid]["color"] = c
            self._palette.set_tiles(self._tiles)
            self._update_canvas_colors()

    def _toggle_collision(self):
        tid = self._palette.selected_tile
        if tid < 0 or tid not in self._tiles:
            return
        self._tiles[tid]["collision"] = not self._tiles[tid]["collision"]
        self._palette.set_tiles(self._tiles)

    def _update_canvas_colors(self):
        colors = {tid: t["color"] for tid, t in self._tiles.items()}
        self._canvas.set_tile_colors(colors)

    def _on_grid_size_changed(self):
        self._canvas.set_grid_size(
            self._grid_w_spin.value(), self._grid_h_spin.value()
        )

    def _clear_map(self):
        self._canvas.clear()
        self._on_map_changed()

    def _on_map_changed(self):
        self.data_changed.emit(self._canvas.to_string())

    # --- Public API for integration ---

    def load_data(self, data_str: str, cell_size: int = 32):
        """Load tilemap data from serialized string."""
        if data_str:
            self._canvas.from_string(data_str)

    def get_data(self) -> str:
        """Get serialized tilemap data."""
        return self._canvas.to_string()

    def get_tiles_dict(self) -> Dict[int, dict]:
        return dict(self._tiles)

    def set_tiles_dict(self, tiles: Dict[int, dict]):
        self._tiles = dict(tiles)
        self._palette.set_tiles(self._tiles)
        self._update_canvas_colors()
        if tiles:
            self._next_id = max(tiles.keys()) + 1
