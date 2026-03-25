"""
Event decorators for Scrawl v2.

These decorators are identical to scrawl v1's API. They mark methods
on Sprite subclasses as event handlers that the engine will call.

Usage:
    class Ball(Sprite):
        @as_main
        def main_loop(self):
            while True:
                self.move(10)
                yield 100

        @on_key("space", "pressed")
        def jump(self):
            self.move_up(50)
"""


def as_main(func):
    """Mark a method as the main task (runs when sprite is created).

    The method should be a generator (use yield to wait):
        @as_main
        def main_loop(self):
            while True:
                self.move(10)
                yield 100  # wait 100ms
    """
    func._is_main = True
    return func


def as_clones(func):
    """Mark a method as the clone task (runs for each cloned sprite).

    Same yield pattern as @as_main.
    """
    func._is_clones = True
    return func


def on_key(key, mode="pressed"):
    """Register a key event handler.

    Args:
        key: Key name (e.g., "space", "left", "a") or pygame key constant
        mode: "pressed", "released", or "held"

    Usage:
        @on_key("space", "pressed")
        def jump(self):
            self.move_up(50)
    """
    def decorator(func):
        func._key_event = (key, mode)
        return func
    return decorator


def on_mouse(button=1, mode="pressed"):
    """Register a mouse event handler.

    Args:
        button: Mouse button (1=left, 2=middle, 3=right)
        mode: "pressed", "released", or "held"
    """
    def decorator(func):
        func._mouse_event = (button, mode)
        return func
    return decorator


def on_broadcast(event_name):
    """Register a broadcast message handler.

    Args:
        event_name: The broadcast message to listen for

    Usage:
        @on_broadcast("game_over")
        def handle_game_over(self):
            self.say("Game Over!")
    """
    def decorator(func):
        func._broadcast_event = event_name
        return func
    return decorator


def on_sprite_clicked(func):
    """Register a handler for when this sprite is clicked.

    Usage:
        @on_sprite_clicked
        def clicked(self):
            self.say("Ouch!")
    """
    func._is_sprite_clicked = True
    return func


def on_edge_collision(edge="any"):
    """Register a handler for screen edge collisions.

    Args:
        edge: "left", "right", "top", "bottom", or "any"

    Usage:
        @on_edge_collision("any")
        def bounce(self):
            self.turn_right(180)
    """
    def decorator(func):
        func._edge_collision = edge
        return func
    return decorator


def on_sprite_collision(sprite_name):
    """Register a handler for collisions with a named sprite.
    Can be stacked:
        @on_sprite_collision("Bat1")
        @on_sprite_collision("Bat2")
        def hit(self):
            ...
    """
    def decorator(func):
        # Support stacking: accumulate into a list
        if not hasattr(func, '_sprite_collision'):
            func._sprite_collision = sprite_name
        elif isinstance(func._sprite_collision, list):
            func._sprite_collision.append(sprite_name)
        else:
            func._sprite_collision = [func._sprite_collision, sprite_name]
        return func
    return decorator
