"""
瓦片地图 - 参考 Godot TileMap。

TileMap 使用 TileSet 中定义的瓦片来构建关卡。

用法:
    tileset = TileSet(tile_size=32)
    tileset.add_tile(0, "ground", "tiles/ground.png")
    tileset.add_tile(1, "wall", "tiles/wall.png", collision=True)
    tileset.add_tile(2, "spike", "tiles/spike.png", collision=True)

    tilemap = TileMap("Level")
    tilemap.tile_set = tileset
    tilemap.set_cell(0, 0, 0)   # 地面
    tilemap.set_cell(1, 0, 1)   # 墙壁

    # 或从列表加载
    level_data = [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
    ]
    tilemap.load_from_array(level_data)
"""

from typing import Dict, List, Optional, Tuple, Set
from .node import Node2D
from .math_utils import Vector2, Rect2
from .signals import Signal


class TileData:
    """单个瓦片类型的数据。"""

    def __init__(self, id: int, name: str = "", texture_path: str = ""):
        self.id = id
        self.name = name
        self.texture_path = texture_path
        self.collision = False
        self.one_way = False
        self.friction = 1.0
        self.custom_data: Dict[str, any] = {}
        self.animation_frames: List[str] = []
        self.animation_speed: float = 5.0
        self.color: Tuple[int, int, int] = (128, 128, 128)


class TileSet:
    """瓦片集 - 参考 Godot TileSet。

    定义可用的瓦片类型及其属性。
    """

    def __init__(self, tile_size: int = 32):
        self.tile_size = tile_size
        self._tiles: Dict[int, TileData] = {}

    def add_tile(self, id: int, name: str = "", texture_path: str = "",
                 collision: bool = False, color: Tuple[int, int, int] = None) -> TileData:
        """添加瓦片类型。"""
        tile = TileData(id, name, texture_path)
        tile.collision = collision
        if color:
            tile.color = color
        self._tiles[id] = tile
        return tile

    def get_tile(self, id: int) -> Optional[TileData]:
        return self._tiles.get(id)

    def remove_tile(self, id: int):
        self._tiles.pop(id, None)

    def get_tile_ids(self) -> List[int]:
        return list(self._tiles.keys())

    @property
    def tile_count(self) -> int:
        return len(self._tiles)


# 瓦片地图中的一个单元格
class _Cell:
    __slots__ = ('tile_id', 'flip_h', 'flip_v', 'transpose')

    def __init__(self, tile_id: int = -1):
        self.tile_id = tile_id
        self.flip_h = False
        self.flip_v = False
        self.transpose = False


class TileMapLayer(Node2D):
    """单层瓦片地图 - 参考 Godot TileMapLayer (Godot 4.3+)。"""

    # 信号
    changed = Signal("changed")

    def __init__(self, name: str = "TileMapLayer"):
        super().__init__(name)
        self.tile_set: Optional[TileSet] = None
        self._cells: Dict[Tuple[int, int], _Cell] = {}
        self.enabled = True
        self.y_sort_enabled = False

    def set_cell(self, x: int, y: int, tile_id: int = -1, flip_h: bool = False, flip_v: bool = False):
        """设置单元格。tile_id=-1 表示清除。"""
        if tile_id < 0:
            self._cells.pop((x, y), None)
        else:
            cell = _Cell(tile_id)
            cell.flip_h = flip_h
            cell.flip_v = flip_v
            self._cells[(x, y)] = cell
        self.changed.emit()

    def get_cell(self, x: int, y: int) -> int:
        """获取单元格的瓦片 ID（-1 表示空）。"""
        cell = self._cells.get((x, y))
        return cell.tile_id if cell else -1

    def erase_cell(self, x: int, y: int):
        self._cells.pop((x, y), None)
        self.changed.emit()

    def clear(self):
        self._cells.clear()
        self.changed.emit()

    def get_used_cells(self) -> List[Tuple[int, int]]:
        return list(self._cells.keys())

    def get_used_cells_by_id(self, tile_id: int) -> List[Tuple[int, int]]:
        return [(x, y) for (x, y), cell in self._cells.items() if cell.tile_id == tile_id]

    def get_used_rect(self) -> Rect2:
        if not self._cells:
            return Rect2()
        min_x = min(x for x, y in self._cells)
        min_y = min(y for x, y in self._cells)
        max_x = max(x for x, y in self._cells)
        max_y = max(y for x, y in self._cells)
        return Rect2(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)


class TileMap(Node2D):
    """瓦片地图 - 参考 Godot TileMap。

    支持多层，每层可以有不同的 Z 顺序。
    """

    # 信号
    changed = Signal("changed")

    def __init__(self, name: str = "TileMap"):
        super().__init__(name)
        self.tile_set: Optional[TileSet] = None
        self._layers: List[TileMapLayer] = []
        self._add_default_layer()

    def _add_default_layer(self):
        layer = TileMapLayer("Layer0")
        self._layers.append(layer)
        self.add_child(layer)

    # === 单层快捷方法（操作 layer 0） ===

    def set_cell(self, x: int, y: int, tile_id: int = -1, layer: int = 0):
        """设置瓦片。"""
        self._ensure_layer(layer)
        self._layers[layer].tile_set = self.tile_set
        self._layers[layer].set_cell(x, y, tile_id)

    def get_cell(self, x: int, y: int, layer: int = 0) -> int:
        if layer < len(self._layers):
            return self._layers[layer].get_cell(x, y)
        return -1

    def erase_cell(self, x: int, y: int, layer: int = 0):
        if layer < len(self._layers):
            self._layers[layer].erase_cell(x, y)

    def clear(self, layer: int = -1):
        """清除瓦片。layer=-1 清除所有层。"""
        if layer < 0:
            for l in self._layers:
                l.clear()
        elif layer < len(self._layers):
            self._layers[layer].clear()

    def get_used_cells(self, layer: int = 0) -> List[Tuple[int, int]]:
        if layer < len(self._layers):
            return self._layers[layer].get_used_cells()
        return []

    # === 多层管理 ===

    def add_layer(self, name: str = "") -> int:
        idx = len(self._layers)
        layer = TileMapLayer(name or f"Layer{idx}")
        layer.tile_set = self.tile_set
        self._layers.append(layer)
        self.add_child(layer)
        return idx

    def get_layers_count(self) -> int:
        return len(self._layers)

    def get_layer(self, index: int) -> Optional[TileMapLayer]:
        if 0 <= index < len(self._layers):
            return self._layers[index]
        return None

    def _ensure_layer(self, index: int):
        while index >= len(self._layers):
            self.add_layer()

    # === 坐标转换 ===

    def world_to_map(self, world_pos: Vector2) -> Tuple[int, int]:
        """世界坐标 -> 地图坐标。"""
        ts = self.tile_set.tile_size if self.tile_set else 32
        return (int(world_pos.x // ts), int(world_pos.y // ts))

    def map_to_world(self, map_x: int, map_y: int) -> Vector2:
        """地图坐标 -> 世界坐标（左上角）。"""
        ts = self.tile_set.tile_size if self.tile_set else 32
        return Vector2(map_x * ts, map_y * ts)

    def map_to_world_center(self, map_x: int, map_y: int) -> Vector2:
        """地图坐标 -> 世界坐标（中心）。"""
        ts = self.tile_set.tile_size if self.tile_set else 32
        return Vector2(map_x * ts + ts / 2, map_y * ts + ts / 2)

    # === 批量加载 ===

    def load_from_array(self, data: List[List[int]], layer: int = 0):
        """从 2D 数组加载瓦片布局。

        Args:
            data: 2D 列表，每个元素是瓦片 ID（-1 表示空）
            layer: 目标层索引
        """
        self._ensure_layer(layer)
        self._layers[layer].clear()
        for y, row in enumerate(data):
            for x, tile_id in enumerate(row):
                if tile_id >= 0:
                    self._layers[layer].set_cell(x, y, tile_id)

    def load_from_string(self, data: str, mapping: Dict[str, int] = None, layer: int = 0):
        """从字符串加载瓦片布局。

        Args:
            data: 多行字符串，每个字符代表一个瓦片
            mapping: 字符 -> 瓦片 ID 映射
            layer: 目标层索引

        用法:
            level = '''
            ####
            #  #
            # G#
            ####
            '''
            tilemap.load_from_string(level, {'#': 1, ' ': 0, 'G': 2})
        """
        if mapping is None:
            mapping = {}

        self._ensure_layer(layer)
        self._layers[layer].clear()

        lines = [line for line in data.strip().split('\n') if line.strip()]
        for y, line in enumerate(lines):
            line = line.strip()
            for x, ch in enumerate(line):
                tile_id = mapping.get(ch, -1)
                if tile_id >= 0:
                    self._layers[layer].set_cell(x, y, tile_id)

    # === 碰撞查询 ===

    def get_collision_cells(self, layer: int = 0) -> List[Tuple[int, int]]:
        """获取所有有碰撞属性的单元格。"""
        if not self.tile_set or layer >= len(self._layers):
            return []

        result = []
        for pos, cell in self._layers[layer]._cells.items():
            tile = self.tile_set.get_tile(cell.tile_id)
            if tile and tile.collision:
                result.append(pos)
        return result

    def is_cell_solid(self, x: int, y: int, layer: int = 0) -> bool:
        """检查单元格是否有碰撞。"""
        tile_id = self.get_cell(x, y, layer)
        if tile_id < 0 or not self.tile_set:
            return False
        tile = self.tile_set.get_tile(tile_id)
        return tile.collision if tile else False
