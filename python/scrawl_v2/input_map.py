"""
输入系统 - 参考 Godot Input / InputMap。

提供:
- InputMap: 动作映射（将多个按键映射到命名动作）
- Input: 全局输入查询
- InputEvent: 输入事件类型

用法:
    # 定义输入映射
    InputMap.add_action("move_left")
    InputMap.action_add_event("move_left", InputEventKey("left"))
    InputMap.action_add_event("move_left", InputEventKey("a"))

    InputMap.add_action("jump")
    InputMap.action_add_event("jump", InputEventKey("space"))
    InputMap.action_add_event("jump", InputEventKey("up"))

    # 游戏中使用
    if Input.is_action_pressed("move_left"):
        player.velocity.x = -speed
    if Input.is_action_just_pressed("jump"):
        player.velocity.y = -jump_force
"""

from typing import Dict, List, Optional, Set
from .math_utils import Vector2


# === 输入事件 ===

class InputEvent:
    """输入事件基类 - 参考 Godot InputEvent。"""

    def __init__(self):
        self.device = 0

    def is_action(self, action: str) -> bool:
        return False

    def is_action_pressed(self, action: str) -> bool:
        return False

    def is_action_released(self, action: str) -> bool:
        return False


class InputEventKey(InputEvent):
    """按键事件 - 参考 Godot InputEventKey。"""

    def __init__(self, key: str = "", pressed: bool = True):
        super().__init__()
        self.key = key.lower()
        self.pressed = pressed
        self.echo = False
        self.shift_pressed = False
        self.ctrl_pressed = False
        self.alt_pressed = False

    def is_action(self, action: str) -> bool:
        return InputMap.event_is_action(self, action)

    def is_action_pressed(self, action: str) -> bool:
        return self.pressed and self.is_action(action)

    def is_action_released(self, action: str) -> bool:
        return not self.pressed and self.is_action(action)


class InputEventMouseButton(InputEvent):
    """鼠标按钮事件 - 参考 Godot InputEventMouseButton。"""

    BUTTON_LEFT = 1
    BUTTON_RIGHT = 2
    BUTTON_MIDDLE = 3
    BUTTON_WHEEL_UP = 4
    BUTTON_WHEEL_DOWN = 5

    def __init__(self, button: int = 1, pressed: bool = True):
        super().__init__()
        self.button_index = button
        self.pressed = pressed
        self.double_click = False
        self.position = Vector2()
        self.global_position = Vector2()


class InputEventMouseMotion(InputEvent):
    """鼠标移动事件 - 参考 Godot InputEventMouseMotion。"""

    def __init__(self):
        super().__init__()
        self.position = Vector2()
        self.global_position = Vector2()
        self.relative = Vector2()
        self.velocity = Vector2()
        self.button_mask = 0


class InputEventJoypadButton(InputEvent):
    """手柄按钮事件。"""

    def __init__(self, button: int = 0, pressed: bool = True):
        super().__init__()
        self.button_index = button
        self.pressed = pressed
        self.pressure = 1.0 if pressed else 0.0


class InputEventJoypadMotion(InputEvent):
    """手柄摇杆事件。"""

    def __init__(self, axis: int = 0, value: float = 0.0):
        super().__init__()
        self.axis = axis
        self.axis_value = value


# === 输入动作映射 ===

class _ActionConfig:
    """动作配置。"""

    def __init__(self, deadzone: float = 0.5):
        self.events: List[InputEvent] = []
        self.deadzone = deadzone


class InputMap:
    """输入动作映射 - 参考 Godot InputMap。

    将命名动作映射到具体的输入事件（按键、鼠标、手柄）。
    """

    _actions: Dict[str, _ActionConfig] = {}

    @classmethod
    def add_action(cls, action: str, deadzone: float = 0.5):
        """注册一个新动作。"""
        if action not in cls._actions:
            cls._actions[action] = _ActionConfig(deadzone)

    @classmethod
    def erase_action(cls, action: str):
        cls._actions.pop(action, None)

    @classmethod
    def has_action(cls, action: str) -> bool:
        return action in cls._actions

    @classmethod
    def action_add_event(cls, action: str, event: InputEvent):
        """为动作添加输入事件。"""
        if action in cls._actions:
            cls._actions[action].events.append(event)

    @classmethod
    def action_erase_event(cls, action: str, event: InputEvent):
        if action in cls._actions:
            cls._actions[action].events = [
                e for e in cls._actions[action].events if e is not event
            ]

    @classmethod
    def action_get_events(cls, action: str) -> List[InputEvent]:
        if action in cls._actions:
            return list(cls._actions[action].events)
        return []

    @classmethod
    def event_is_action(cls, event: InputEvent, action: str) -> bool:
        """检查事件是否属于某个动作。"""
        if action not in cls._actions:
            return False
        for mapped_event in cls._actions[action].events:
            if type(event) == type(mapped_event):
                if isinstance(event, InputEventKey) and isinstance(mapped_event, InputEventKey):
                    if event.key == mapped_event.key:
                        return True
                elif isinstance(event, InputEventMouseButton) and isinstance(mapped_event, InputEventMouseButton):
                    if event.button_index == mapped_event.button_index:
                        return True
                elif isinstance(event, InputEventJoypadButton) and isinstance(mapped_event, InputEventJoypadButton):
                    if event.button_index == mapped_event.button_index:
                        return True
        return False

    @classmethod
    def get_actions(cls) -> List[str]:
        return list(cls._actions.keys())

    @classmethod
    def load_default_actions(cls):
        """加载默认动作映射（常用的移动和交互动作）。"""
        # 移动
        cls.add_action("move_left")
        cls.action_add_event("move_left", InputEventKey("left"))
        cls.action_add_event("move_left", InputEventKey("a"))

        cls.add_action("move_right")
        cls.action_add_event("move_right", InputEventKey("right"))
        cls.action_add_event("move_right", InputEventKey("d"))

        cls.add_action("move_up")
        cls.action_add_event("move_up", InputEventKey("up"))
        cls.action_add_event("move_up", InputEventKey("w"))

        cls.add_action("move_down")
        cls.action_add_event("move_down", InputEventKey("down"))
        cls.action_add_event("move_down", InputEventKey("s"))

        # 交互
        cls.add_action("jump")
        cls.action_add_event("jump", InputEventKey("space"))

        cls.add_action("action")
        cls.action_add_event("action", InputEventKey("return"))

        cls.add_action("cancel")
        cls.action_add_event("cancel", InputEventKey("escape"))

        cls.add_action("attack")
        cls.action_add_event("attack", InputEventMouseButton(1))


# === 全局输入查询 ===

class Input:
    """全局输入状态 - 参考 Godot Input 单例。

    用法:
        if Input.is_action_pressed("move_right"):
            velocity.x += speed

        if Input.is_action_just_pressed("jump"):
            velocity.y = -jump_force

        direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")
    """

    _pressed_keys: Set[str] = set()
    _just_pressed_keys: Set[str] = set()
    _just_released_keys: Set[str] = set()
    _mouse_position = Vector2()
    _mouse_buttons: Set[int] = set()
    _just_pressed_mouse: Set[int] = set()

    @classmethod
    def is_key_pressed(cls, key: str) -> bool:
        return key.lower() in cls._pressed_keys

    @classmethod
    def is_action_pressed(cls, action: str) -> bool:
        """检查动作是否被按住。"""
        if not InputMap.has_action(action):
            return False
        for event in InputMap.action_get_events(action):
            if isinstance(event, InputEventKey):
                if event.key in cls._pressed_keys:
                    return True
            elif isinstance(event, InputEventMouseButton):
                if event.button_index in cls._mouse_buttons:
                    return True
        return False

    @classmethod
    def is_action_just_pressed(cls, action: str) -> bool:
        """检查动作是否在本帧刚刚按下。"""
        if not InputMap.has_action(action):
            return False
        for event in InputMap.action_get_events(action):
            if isinstance(event, InputEventKey):
                if event.key in cls._just_pressed_keys:
                    return True
            elif isinstance(event, InputEventMouseButton):
                if event.button_index in cls._just_pressed_mouse:
                    return True
        return False

    @classmethod
    def is_action_just_released(cls, action: str) -> bool:
        """检查动作是否在本帧刚刚释放。"""
        if not InputMap.has_action(action):
            return False
        for event in InputMap.action_get_events(action):
            if isinstance(event, InputEventKey):
                if event.key in cls._just_released_keys:
                    return True
        return False

    @classmethod
    def get_axis(cls, negative_action: str, positive_action: str) -> float:
        """获取轴值（-1 到 1）。"""
        value = 0.0
        if cls.is_action_pressed(negative_action):
            value -= 1.0
        if cls.is_action_pressed(positive_action):
            value += 1.0
        return value

    @classmethod
    def get_vector(cls, neg_x: str, pos_x: str, neg_y: str, pos_y: str) -> Vector2:
        """获取 2D 输入向量（已归一化）。"""
        v = Vector2(
            cls.get_axis(neg_x, pos_x),
            cls.get_axis(neg_y, pos_y)
        )
        if v.length() > 1.0:
            return v.normalized()
        return v

    @classmethod
    def get_mouse_position(cls) -> Vector2:
        return Vector2(cls._mouse_position.x, cls._mouse_position.y)

    @classmethod
    def is_mouse_button_pressed(cls, button: int) -> bool:
        return button in cls._mouse_buttons

    @classmethod
    def _update(cls):
        """帧结束时清理 just_pressed 状态（由引擎调用）。"""
        cls._just_pressed_keys.clear()
        cls._just_released_keys.clear()
        cls._just_pressed_mouse.clear()

    @classmethod
    def _on_key_press(cls, key: str):
        key = key.lower()
        if key not in cls._pressed_keys:
            cls._just_pressed_keys.add(key)
        cls._pressed_keys.add(key)

    @classmethod
    def _on_key_release(cls, key: str):
        key = key.lower()
        cls._pressed_keys.discard(key)
        cls._just_released_keys.add(key)

    @classmethod
    def _on_mouse_button(cls, button: int, pressed: bool):
        if pressed:
            cls._mouse_buttons.add(button)
            cls._just_pressed_mouse.add(button)
        else:
            cls._mouse_buttons.discard(button)

    @classmethod
    def _on_mouse_motion(cls, x: float, y: float):
        cls._mouse_position = Vector2(x, y)
