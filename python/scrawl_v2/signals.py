"""
信号系统 - 参考 Godot 的 Signal 机制。

提供类型安全的信号连接和发射系统，替代简单的广播机制。

用法:
    class Player(Sprite):
        health_changed = Signal("health_changed", int)
        died = Signal("died")

        def take_damage(self, amount):
            self.health -= amount
            self.health_changed.emit(self.health)
            if self.health <= 0:
                self.died.emit()

    player = Player()
    player.health_changed.connect(hud.update_health)
    player.died.connect(game.game_over)
"""

from typing import Callable, List, Any, Optional
import weakref


class Signal:
    """信号对象 - 参考 Godot Signal。

    与 Godot 类似，信号定义在类级别，每个实例拥有独立的连接列表。
    """

    def __init__(self, name: str = "", *arg_types):
        self.name = name
        self.arg_types = arg_types
        self._attr_name = None  # 由 __set_name__ 设置

    def __set_name__(self, owner, name):
        self._attr_name = f"_signal_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # 每个实例拥有独立的 SignalInstance
        if not hasattr(obj, self._attr_name):
            setattr(obj, self._attr_name, SignalInstance(self.name or self._attr_name))
        return getattr(obj, self._attr_name)

    def __set__(self, obj, value):
        raise AttributeError("Cannot assign to signal")


class SignalInstance:
    """信号实例 - 存储某个对象上信号的所有连接。"""

    def __init__(self, name: str):
        self.name = name
        self._connections: List[_Connection] = []

    def connect(self, callable_or_method: Callable, oneshot: bool = False):
        """连接一个回调函数到此信号。

        Args:
            callable_or_method: 当信号发射时调用的函数
            oneshot: 如果为 True，信号触发一次后自动断开连接
        """
        conn = _Connection(callable_or_method, oneshot=oneshot)
        self._connections.append(conn)
        return self

    def disconnect(self, callable_or_method: Callable):
        """断开一个回调函数的连接。"""
        self._connections = [c for c in self._connections if c.callback != callable_or_method]

    def emit(self, *args, **kwargs):
        """发射信号，调用所有已连接的回调。"""
        to_remove = []
        for conn in self._connections:
            try:
                conn.callback(*args, **kwargs)
                if conn.oneshot:
                    to_remove.append(conn)
            except Exception as e:
                print(f"[Signal] Error in '{self.name}' handler: {e}")
        for conn in to_remove:
            self._connections.remove(conn)

    def is_connected(self, callable_or_method: Callable) -> bool:
        return any(c.callback == callable_or_method for c in self._connections)

    def get_connections(self) -> int:
        return len(self._connections)

    def clear(self):
        """断开所有连接。"""
        self._connections.clear()


class _Connection:
    """内部连接记录。"""

    __slots__ = ('callback', 'oneshot')

    def __init__(self, callback: Callable, oneshot: bool = False):
        self.callback = callback
        self.oneshot = oneshot
