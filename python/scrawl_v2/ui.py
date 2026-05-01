"""
UI 系统 - 参考 Godot Control 节点体系。

提供游戏内 UI 组件：Label、Button、ProgressBar、Panel、TextInput 等。

用法:
    # 创建 HUD
    hud = CanvasLayer("HUD")

    health_bar = ProgressBar("HealthBar")
    health_bar.position = Vector2(20, 20)
    health_bar.size = Vector2(200, 20)
    health_bar.value = 80
    hud.add_child(health_bar)

    score_label = Label("Score")
    score_label.text = "Score: 0"
    score_label.position = Vector2(20, 50)
    hud.add_child(score_label)

    pause_btn = Button("PauseBtn")
    pause_btn.text = "Pause"
    pause_btn.position = Vector2(700, 20)
    pause_btn.pressed.connect(toggle_pause)
    hud.add_child(pause_btn)
"""

from typing import Optional, Tuple, List, Callable
from .node import Node, Node2D
from .math_utils import Vector2, Rect2
from .signals import Signal


# === CanvasLayer ===

class CanvasLayer(Node):
    """画布层 - 参考 Godot CanvasLayer。

    不受 Camera2D 影响，适合用于 HUD、菜单等 UI 层。
    """

    def __init__(self, name: str = "CanvasLayer"):
        super().__init__(name)
        self.layer = 1
        self.follow_viewport = False
        self.offset = Vector2()


# === Control 基类 ===

class Control(Node2D):
    """UI 控件基类 - 参考 Godot Control。

    所有 UI 组件的基类，提供布局和主题支持。
    """

    # 锚点常量
    ANCHOR_BEGIN = 0
    ANCHOR_END = 1
    ANCHOR_CENTER = 0.5

    # 尺寸标志
    SIZE_EXPAND = 1
    SIZE_FILL = 2
    SIZE_SHRINK_CENTER = 4

    # 信号
    resized = Signal("resized")
    focus_entered = Signal("focus_entered")
    focus_exited = Signal("focus_exited")
    mouse_entered = Signal("mouse_entered")
    mouse_exited = Signal("mouse_exited")

    def __init__(self, name: str = "Control"):
        super().__init__(name)
        self._size = Vector2(100, 30)
        self._min_size = Vector2()
        self._anchor_left = 0.0
        self._anchor_top = 0.0
        self._anchor_right = 0.0
        self._anchor_bottom = 0.0
        self._margin_left = 0
        self._margin_top = 0
        self._margin_right = 0
        self._margin_bottom = 0
        self.focus_mode = 0  # 0=none, 1=click, 2=all
        self.mouse_filter = 0  # 0=stop, 1=pass, 2=ignore
        self._has_focus = False
        self.tooltip_text = ""

        # 主题
        self.theme_type = ""
        self._custom_colors: dict = {}
        self._custom_fonts: dict = {}

    @property
    def size(self) -> Vector2:
        return self._size

    @size.setter
    def size(self, value):
        if isinstance(value, (tuple, list)):
            self._size = Vector2(float(value[0]), float(value[1]))
        else:
            self._size = value
        self.resized.emit()

    @property
    def min_size(self) -> Vector2:
        return self._min_size

    @min_size.setter
    def min_size(self, value):
        if isinstance(value, (tuple, list)):
            self._min_size = Vector2(float(value[0]), float(value[1]))
        else:
            self._min_size = value

    def get_rect(self) -> Rect2:
        return Rect2(self._position.x, self._position.y, self._size.x, self._size.y)

    def get_global_rect(self) -> Rect2:
        gp = self.global_position
        return Rect2(gp.x, gp.y, self._size.x, self._size.y)

    def has_point(self, point: Vector2) -> bool:
        return self.get_global_rect().has_point(point)

    def grab_focus(self):
        self._has_focus = True
        self.focus_entered.emit()

    def release_focus(self):
        self._has_focus = False
        self.focus_exited.emit()

    def has_focus(self) -> bool:
        return self._has_focus

    def set_custom_color(self, name: str, color: Tuple[int, int, int, int]):
        self._custom_colors[name] = color

    def get_custom_color(self, name: str) -> Optional[Tuple]:
        return self._custom_colors.get(name)


# === Label ===

class Label(Control):
    """文本标签 - 参考 Godot Label。"""

    def __init__(self, name: str = "Label"):
        super().__init__(name)
        self.text = ""
        self.font_size = 16
        self.font_color = (255, 255, 255, 255)
        self.align = "left"  # "left", "center", "right"
        self.valign = "top"  # "top", "center", "bottom"
        self.autowrap = False
        self.uppercase = False
        self.outline_size = 0
        self.outline_color = (0, 0, 0, 255)
        self.shadow_color = (0, 0, 0, 0)
        self.shadow_offset = Vector2(1, 1)


# === Button ===

class Button(Control):
    """按钮 - 参考 Godot Button。"""

    # 信号
    pressed = Signal("pressed")
    toggled = Signal("toggled")
    button_down = Signal("button_down")
    button_up = Signal("button_up")

    def __init__(self, name: str = "Button"):
        super().__init__(name)
        self.text = ""
        self.icon = None
        self.flat = False
        self.toggle_mode = False
        self._pressed = False
        self._hovered = False
        self.disabled = False

        self.font_size = 16
        self.font_color = (255, 255, 255, 255)
        self.bg_color = (60, 60, 60, 255)
        self.bg_hover_color = (80, 80, 80, 255)
        self.bg_pressed_color = (40, 40, 40, 255)
        self.border_color = (100, 100, 100, 255)
        self.border_width = 1
        self.corner_radius = 4

    @property
    def button_pressed(self) -> bool:
        return self._pressed

    @button_pressed.setter
    def button_pressed(self, value: bool):
        if self._pressed != value:
            self._pressed = value
            if self.toggle_mode:
                self.toggled.emit(value)

    def _on_click(self):
        if self.disabled:
            return
        if self.toggle_mode:
            self.button_pressed = not self.button_pressed
        self.pressed.emit()


# === TextureButton ===

class TextureButton(Button):
    """纹理按钮 - 参考 Godot TextureButton。"""

    def __init__(self, name: str = "TextureButton"):
        super().__init__(name)
        self.texture_normal = None
        self.texture_pressed = None
        self.texture_hover = None
        self.texture_disabled = None
        self.texture_focused = None
        self.stretch_mode = 0  # 0=scale, 1=tile, 2=keep, 3=keep_centered


# === ProgressBar ===

class ProgressBar(Control):
    """进度条 - 参考 Godot ProgressBar。"""

    # 信号
    value_changed = Signal("value_changed")

    def __init__(self, name: str = "ProgressBar"):
        super().__init__(name)
        self._value = 0.0
        self.min_value = 0.0
        self.max_value = 100.0
        self.step = 0.01
        self.rounded = False
        self.show_percentage = True
        self.fill_mode = 0  # 0=left_to_right, 1=right_to_left, 2=top_to_bottom, 3=bottom_to_top

        self.bg_color = (40, 40, 40, 255)
        self.fill_color = (80, 180, 80, 255)
        self.border_color = (100, 100, 100, 255)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float):
        v = max(self.min_value, min(self.max_value, float(v)))
        if self._value != v:
            self._value = v
            self.value_changed.emit(v)

    @property
    def ratio(self) -> float:
        """获取 0~1 之间的比例值。"""
        range_ = self.max_value - self.min_value
        if range_ == 0:
            return 0
        return (self._value - self.min_value) / range_


# === TextEdit ===

class TextEdit(Control):
    """多行文本编辑 - 参考 Godot TextEdit。"""

    # 信号
    text_changed = Signal("text_changed")
    text_submitted = Signal("text_submitted")

    def __init__(self, name: str = "TextEdit"):
        super().__init__(name)
        self.text = ""
        self.placeholder_text = ""
        self.editable = True
        self.wrap_mode = 0  # 0=none, 1=boundary
        self.font_size = 14
        self.font_color = (255, 255, 255, 255)
        self.bg_color = (30, 30, 30, 255)
        self.caret_color = (255, 255, 255, 255)
        self.selection_color = (60, 120, 200, 150)
        self._cursor_line = 0
        self._cursor_column = 0

    def set_text(self, text: str):
        self.text = text
        self.text_changed.emit()

    def get_line_count(self) -> int:
        return self.text.count('\n') + 1

    def clear(self):
        self.text = ""
        self.text_changed.emit()


# === LineEdit ===

class LineEdit(Control):
    """单行文本输入 - 参考 Godot LineEdit。"""

    # 信号
    text_changed = Signal("text_changed")
    text_submitted = Signal("text_submitted")

    def __init__(self, name: str = "LineEdit"):
        super().__init__(name)
        self.text = ""
        self.placeholder_text = "Enter text..."
        self.editable = True
        self.secret = False  # 密码模式
        self.max_length = 0  # 0=无限制
        self.font_size = 14
        self.font_color = (255, 255, 255, 255)
        self.bg_color = (30, 30, 30, 255)
        self.border_color = (100, 100, 100, 255)


# === Panel ===

class Panel(Control):
    """面板 - 参考 Godot Panel。"""

    def __init__(self, name: str = "Panel"):
        super().__init__(name)
        self.bg_color = (50, 50, 50, 200)
        self.border_color = (80, 80, 80, 255)
        self.border_width = 1
        self.corner_radius = 0


# === 容器 ===

class Container(Control):
    """容器基类 - 参考 Godot Container。"""

    def __init__(self, name: str = "Container"):
        super().__init__(name)

    def _arrange_children(self):
        """重新排列子节点（由子类实现）。"""
        pass


class HBoxContainer(Container):
    """水平排列容器 - 参考 Godot HBoxContainer。"""

    def __init__(self, name: str = "HBoxContainer"):
        super().__init__(name)
        self.separation = 4

    def _arrange_children(self):
        x_offset = 0
        for child in self._children:
            if isinstance(child, Control):
                child._position = Vector2(x_offset, 0)
                x_offset += child._size.x + self.separation


class VBoxContainer(Container):
    """垂直排列容器 - 参考 Godot VBoxContainer。"""

    def __init__(self, name: str = "VBoxContainer"):
        super().__init__(name)
        self.separation = 4

    def _arrange_children(self):
        y_offset = 0
        for child in self._children:
            if isinstance(child, Control):
                child._position = Vector2(0, y_offset)
                y_offset += child._size.y + self.separation


class GridContainer(Container):
    """网格排列容器 - 参考 Godot GridContainer。"""

    def __init__(self, name: str = "GridContainer"):
        super().__init__(name)
        self.columns = 2
        self.h_separation = 4
        self.v_separation = 4

    def _arrange_children(self):
        controls = [c for c in self._children if isinstance(c, Control)]
        for i, child in enumerate(controls):
            col = i % self.columns
            row = i // self.columns
            child._position = Vector2(
                col * (child._size.x + self.h_separation),
                row * (child._size.y + self.v_separation)
            )


# === NinePatchRect ===

class NinePatchRect(Control):
    """九宫格纹理矩形 - 参考 Godot NinePatchRect。"""

    def __init__(self, name: str = "NinePatchRect"):
        super().__init__(name)
        self.texture = None
        self.patch_margin_left = 0
        self.patch_margin_right = 0
        self.patch_margin_top = 0
        self.patch_margin_bottom = 0
        self.draw_center = True


# === TextureRect ===

class TextureRect(Control):
    """纹理矩形 - 参考 Godot TextureRect。"""

    def __init__(self, name: str = "TextureRect"):
        super().__init__(name)
        self.texture = None
        self.stretch_mode = 0  # 0=scale, 1=tile, 2=keep, 3=keep_centered, 4=keep_aspect
        self.flip_h = False
        self.flip_v = False


# === ColorRect ===

class ColorRect(Control):
    """颜色矩形 - 参考 Godot ColorRect。"""

    def __init__(self, name: str = "ColorRect"):
        super().__init__(name)
        self.color = (255, 255, 255, 255)
