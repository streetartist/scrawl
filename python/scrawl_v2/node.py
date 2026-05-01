"""
节点系统 - 参考 Godot Node/Node2D 树形架构。

提供游戏对象的层级管理，所有游戏对象都是节点。

节点类型层级:
    Node (基础节点)
    ├── Node2D (2D 变换节点)
    │   ├── Sprite (精灵 - 兼容 v1)
    │   ├── Camera2D (2D 摄像机)
    │   ├── Light2D (2D 光源)
    │   ├── RayCast2D (射线检测)
    │   ├── Area2D (区域检测)
    │   ├── CollisionShape2D (碰撞形状)
    │   ├── TileMap (瓦片地图)
    │   ├── ParticleEmitter2D (粒子发射器)
    │   ├── AnimatedSprite (动画精灵)
    │   └── Path2D (路径)
    ├── Timer (计时器)
    ├── AudioPlayer (音频播放器)
    └── Control (UI 控件基类)
"""

from typing import List, Optional, Dict, Any, Callable
from .math_utils import Vector2, Transform2D
from .signals import Signal


class Node:
    """基础节点 - 参考 Godot Node。

    所有游戏对象的基类，提供树形层级管理。
    """

    # 信号
    tree_entered = Signal("tree_entered")
    tree_exited = Signal("tree_exited")
    ready_signal = Signal("ready")
    child_entered = Signal("child_entered")

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__
        self._parent: Optional['Node'] = None
        self._children: List['Node'] = []
        self._groups: List[str] = []
        self._is_ready = False
        self._is_in_tree = False
        self._process_enabled = True
        self._physics_process_enabled = True
        self._paused = False
        self._meta: Dict[str, Any] = {}

    # === 树操作 ===

    def add_child(self, node: 'Node'):
        """添加子节点。"""
        if node._parent:
            node._parent.remove_child(node)
        node._parent = self
        self._children.append(node)
        node._is_in_tree = self._is_in_tree
        if node._is_in_tree:
            node._enter_tree()
        self.child_entered.emit(node)

    def remove_child(self, node: 'Node'):
        """移除子节点。"""
        if node in self._children:
            self._children.remove(node)
            if node._is_in_tree:
                node._exit_tree()
            node._parent = None

    def get_child(self, index: int) -> Optional['Node']:
        if 0 <= index < len(self._children):
            return self._children[index]
        return None

    def get_child_count(self) -> int:
        return len(self._children)

    def get_children(self) -> List['Node']:
        return list(self._children)

    def get_parent(self) -> Optional['Node']:
        return self._parent

    def get_node(self, path: str) -> Optional['Node']:
        """通过路径获取节点（简化版 Godot NodePath）。

        支持: "ChildName", "Child/GrandChild", ".." (父节点), "." (自身)
        """
        if path == ".":
            return self
        if path == "..":
            return self._parent

        parts = path.split("/")
        current = self
        for part in parts:
            if part == "..":
                current = current._parent
            elif part == ".":
                continue
            else:
                found = None
                for child in current._children:
                    if child.name == part:
                        found = child
                        break
                if found is None:
                    return None
                current = found
        return current

    def find_child(self, name: str, recursive: bool = True) -> Optional['Node']:
        """按名称查找子节点。"""
        for child in self._children:
            if child.name == name:
                return child
            if recursive:
                result = child.find_child(name, recursive=True)
                if result:
                    return result
        return None

    def find_children(self, pattern: str = "*", type_name: str = "", recursive: bool = True) -> List['Node']:
        """查找所有匹配的子节点。"""
        results = []
        for child in self._children:
            match = True
            if pattern != "*" and child.name != pattern:
                match = False
            if type_name and child.__class__.__name__ != type_name:
                match = False
            if match:
                results.append(child)
            if recursive:
                results.extend(child.find_children(pattern, type_name, recursive))
        return results

    def get_index(self) -> int:
        if self._parent:
            return self._parent._children.index(self)
        return -1

    def move_child(self, child: 'Node', new_index: int):
        if child in self._children:
            self._children.remove(child)
            self._children.insert(new_index, child)

    def reparent(self, new_parent: 'Node'):
        if self._parent:
            self._parent.remove_child(self)
        new_parent.add_child(self)

    # === 分组 ===

    def add_to_group(self, group: str):
        if group not in self._groups:
            self._groups.append(group)

    def remove_from_group(self, group: str):
        if group in self._groups:
            self._groups.remove(group)

    def is_in_group(self, group: str) -> bool:
        return group in self._groups

    def get_groups(self) -> List[str]:
        return list(self._groups)

    # === 生命周期 ===

    def _enter_tree(self):
        """节点进入场景树时调用。"""
        self._is_in_tree = True
        self.tree_entered.emit()
        for child in self._children:
            child._enter_tree()
        if not self._is_ready:
            self._is_ready = True
            self._ready()
            self.ready_signal.emit()

    def _exit_tree(self):
        """节点退出场景树时调用。"""
        for child in self._children:
            child._exit_tree()
        self._is_in_tree = False
        self.tree_exited.emit()

    def _ready(self):
        """节点就绪（可重写）。首次进入场景树时调用一次。"""
        pass

    def _process(self, delta: float):
        """每帧处理（可重写）。

        Args:
            delta: 距上一帧的时间（秒）
        """
        pass

    def _physics_process(self, delta: float):
        """物理帧处理（可重写）。固定时间步长调用。

        Args:
            delta: 固定时间步长（秒）
        """
        pass

    def _process_tree(self, delta: float):
        """递归处理整个子树。"""
        if self._process_enabled and not self._paused:
            self._process(delta)
            for child in self._children:
                child._process_tree(delta)

    def _physics_process_tree(self, delta: float):
        """递归物理处理整个子树。"""
        if self._physics_process_enabled and not self._paused:
            self._physics_process(delta)
            for child in self._children:
                child._physics_process_tree(delta)

    # === 元数据 ===

    def set_meta(self, key: str, value: Any):
        self._meta[key] = value

    def get_meta(self, key: str, default: Any = None) -> Any:
        return self._meta.get(key, default)

    def has_meta(self, key: str) -> bool:
        return key in self._meta

    # === 工具方法 ===

    def queue_free(self):
        """请求在帧结束时释放此节点。"""
        if self._parent:
            self._parent.remove_child(self)

    def is_inside_tree(self) -> bool:
        return self._is_in_tree

    def get_tree_string(self, indent: int = 0) -> str:
        """调试用：打印节点树。"""
        result = " " * indent + f"[{self.__class__.__name__}] {self.name}\n"
        for child in self._children:
            result += child.get_tree_string(indent + 2)
        return result

    def __repr__(self):
        return f"<{self.__class__.__name__} name='{self.name}'>"


class Node2D(Node):
    """2D 节点 - 参考 Godot Node2D。

    带有 2D 变换（位置、旋转、缩放）的节点。
    """

    def __init__(self, name: str = ""):
        super().__init__(name)
        self._position = Vector2()
        self._rotation = 0.0  # 弧度
        self._scale = Vector2(1, 1)
        self._z_index = 0
        self._z_as_relative = True
        self._visible = True
        self._modulate = (255, 255, 255, 255)  # RGBA

    # === 位置 ===

    @property
    def position(self) -> Vector2:
        return self._position

    @position.setter
    def position(self, value: Vector2):
        if isinstance(value, (tuple, list)):
            self._position = Vector2(float(value[0]), float(value[1]))
        else:
            self._position = value

    @property
    def global_position(self) -> Vector2:
        """全局坐标。"""
        if self._parent and isinstance(self._parent, Node2D):
            return self._parent.global_position + self._position
        return Vector2(self._position.x, self._position.y)

    @global_position.setter
    def global_position(self, value: Vector2):
        if self._parent and isinstance(self._parent, Node2D):
            self._position = value - self._parent.global_position
        else:
            self._position = value

    # === 旋转 ===

    @property
    def rotation(self) -> float:
        """旋转角度（弧度）。"""
        return self._rotation

    @rotation.setter
    def rotation(self, value: float):
        self._rotation = float(value)

    @property
    def rotation_degrees(self) -> float:
        """旋转角度（度数）。"""
        import math
        return math.degrees(self._rotation)

    @rotation_degrees.setter
    def rotation_degrees(self, value: float):
        import math
        self._rotation = math.radians(value)

    @property
    def global_rotation(self) -> float:
        if self._parent and isinstance(self._parent, Node2D):
            return self._parent.global_rotation + self._rotation
        return self._rotation

    # === 缩放 ===

    @property
    def scale(self) -> Vector2:
        return self._scale

    @scale.setter
    def scale(self, value):
        if isinstance(value, (tuple, list)):
            self._scale = Vector2(float(value[0]), float(value[1]))
        elif isinstance(value, (int, float)):
            self._scale = Vector2(float(value), float(value))
        else:
            self._scale = value

    @property
    def global_scale(self) -> Vector2:
        if self._parent and isinstance(self._parent, Node2D):
            p = self._parent.global_scale
            return Vector2(p.x * self._scale.x, p.y * self._scale.y)
        return Vector2(self._scale.x, self._scale.y)

    # === Z 顺序 ===

    @property
    def z_index(self) -> int:
        return self._z_index

    @z_index.setter
    def z_index(self, value: int):
        self._z_index = value

    # === 可见性 ===

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        self._visible = value

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False

    @property
    def modulate(self):
        return self._modulate

    @modulate.setter
    def modulate(self, value):
        self._modulate = value

    # === 变换 ===

    def get_transform(self) -> Transform2D:
        return Transform2D(self._rotation, self._position, self._scale)

    def get_global_transform(self) -> Transform2D:
        return Transform2D(self.global_rotation, self.global_position, self.global_scale)

    def to_local(self, global_point: Vector2) -> Vector2:
        """将全局坐标转换为局部坐标。"""
        return self.get_global_transform().xform_inv(global_point)

    def to_global(self, local_point: Vector2) -> Vector2:
        """将局部坐标转换为全局坐标。"""
        return self.get_global_transform().xform(local_point)

    def look_at(self, target: Vector2):
        """面向目标位置。"""
        import math
        diff = target - self.global_position
        self._rotation = math.atan2(diff.y, diff.x)

    def rotate(self, angle: float):
        """旋转指定弧度。"""
        self._rotation += angle

    def translate(self, offset: Vector2):
        """平移。"""
        self._position = self._position + offset

    def apply_scale(self, ratio: Vector2):
        """应用缩放。"""
        self._scale = Vector2(self._scale.x * ratio.x, self._scale.y * ratio.y)
