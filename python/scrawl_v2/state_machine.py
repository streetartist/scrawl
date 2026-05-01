"""
状态机 - 参考 Godot AnimationTree 中的 StateMachine。

提供通用的有限状态机（FSM），可用于游戏逻辑、AI、动画状态管理。

用法:
    class PlayerStateMachine(StateMachine):
        def __init__(self):
            super().__init__()
            self.add_state("idle", IdleState())
            self.add_state("run", RunState())
            self.add_state("jump", JumpState())
            self.add_state("attack", AttackState())

            self.add_transition("idle", "run", lambda: Input.is_action_pressed("move_right"))
            self.add_transition("run", "idle", lambda: not Input.is_action_pressed("move_right"))
            self.add_transition("idle", "jump", lambda: Input.is_action_just_pressed("jump"))
            self.add_transition("run", "jump", lambda: Input.is_action_just_pressed("jump"))

            self.start("idle")

    class IdleState(State):
        def enter(self, owner):
            owner.play_animation("idle")

        def update(self, owner, delta):
            pass

        def exit(self, owner):
            pass
"""

from typing import Dict, Optional, Callable, List, Any
from .node import Node
from .signals import Signal


class State:
    """状态基类。

    重写 enter/update/exit 方法来定义状态行为。
    """

    def enter(self, owner):
        """进入状态时调用。"""
        pass

    def exit(self, owner):
        """退出状态时调用。"""
        pass

    def update(self, owner, delta: float):
        """每帧更新（在 _process 中调用）。"""
        pass

    def physics_update(self, owner, delta: float):
        """物理帧更新（在 _physics_process 中调用）。"""
        pass

    def handle_input(self, owner, event):
        """处理输入事件。"""
        pass


class _Transition:
    """状态转换。"""

    def __init__(self, from_state: str, to_state: str, condition: Callable = None):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition


class StateMachine(Node):
    """有限状态机 - 参考 Godot StateMachine。"""

    # 信号
    state_changed = Signal("state_changed")

    def __init__(self, name: str = "StateMachine"):
        super().__init__(name)
        self._states: Dict[str, State] = {}
        self._transitions: List[_Transition] = []
        self._current_state: Optional[str] = None
        self._previous_state: Optional[str] = None
        self._owner = None  # 状态机的所有者

    @property
    def current_state(self) -> Optional[str]:
        return self._current_state

    @property
    def previous_state(self) -> Optional[str]:
        return self._previous_state

    def add_state(self, name: str, state: State):
        """添加状态。"""
        self._states[name] = state

    def remove_state(self, name: str):
        if name != self._current_state:
            self._states.pop(name, None)

    def has_state(self, name: str) -> bool:
        return name in self._states

    def get_state(self, name: str) -> Optional[State]:
        return self._states.get(name)

    def add_transition(self, from_state: str, to_state: str, condition: Callable = None):
        """添加状态转换规则。

        Args:
            from_state: 源状态名
            to_state: 目标状态名
            condition: 条件函数（返回 True 时触发转换）
        """
        self._transitions.append(_Transition(from_state, to_state, condition))

    def start(self, initial_state: str):
        """启动状态机。"""
        self._owner = self._parent
        if initial_state in self._states:
            self._current_state = initial_state
            self._states[initial_state].enter(self._owner)
            self.state_changed.emit(initial_state)

    def transition_to(self, target_state: str):
        """强制转换到指定状态。"""
        if target_state not in self._states:
            return
        if self._current_state == target_state:
            return

        if self._current_state and self._current_state in self._states:
            self._states[self._current_state].exit(self._owner)

        self._previous_state = self._current_state
        self._current_state = target_state
        self._states[target_state].enter(self._owner)
        self.state_changed.emit(target_state)

    def _process(self, delta: float):
        if not self._current_state:
            return

        owner = self._owner or self._parent

        # 检查自动转换
        for trans in self._transitions:
            if trans.from_state == self._current_state and trans.condition:
                try:
                    if trans.condition():
                        self.transition_to(trans.to_state)
                        return
                except Exception:
                    pass

        # 更新当前状态
        state = self._states.get(self._current_state)
        if state:
            state.update(owner, delta)

    def _physics_process(self, delta: float):
        if not self._current_state:
            return

        owner = self._owner or self._parent
        state = self._states.get(self._current_state)
        if state:
            state.physics_update(owner, delta)

    def handle_input(self, event):
        if self._current_state:
            owner = self._owner or self._parent
            state = self._states.get(self._current_state)
            if state:
                state.handle_input(owner, event)

    def get_state_names(self) -> list:
        return list(self._states.keys())
