"""
Scrawl Demo - Basic Sprite Movement

This demo verifies:
1. Game window opens via Bevy
2. Sprite renders and moves
3. Keyboard input works (@on_key decorator)
4. Broadcast messaging works
5. Edge collision detection works

Run with: python examples/basic_movement.py
(Requires: maturin develop --release)
"""

from scrawl import *


class Ball(Sprite2D):
    """A ball that bounces around the screen."""

    def __init__(self):
        super().__init__()
        self.name = "Ball"
        self.x = 400.0
        self.y = 300.0
        self.direction = 45.0
        self.size = 1.0
        self.speed = 3.0
        self.color = (100, 200, 255)

    @as_main
    def main_loop(self):
        """Main loop: move forward continuously."""
        while True:
            self.move(self.speed)
            yield 16  # ~60fps

    @on_key("space", "pressed")
    def speed_boost(self):
        """Press space to boost speed temporarily."""
        old_speed = self.speed
        self.speed = 8.0
        yield 500  # boost for 500ms
        self.speed = old_speed

    @on_key("left", "held")
    def turn_left_handler(self):
        self.turn_left(3)

    @on_key("right", "held")
    def turn_right_handler(self):
        self.turn_right(3)

    @on_edge_collision("any")
    def bounce(self):
        """Bounce off screen edges."""
        self.turn_right(180)
        self.move(10)


class Player(Sprite2D):
    """A player controlled by WASD keys."""

    def __init__(self):
        super().__init__()
        self.name = "Player"
        self.x = 200.0
        self.y = 200.0
        self.size = 1.0
        self.color = (255, 100, 100)

    @on_key("w", "held")
    def move_up_handler(self):
        self.move_up(5)

    @on_key("s", "held")
    def move_down_handler(self):
        self.move_down(5)

    @on_key("a", "held")
    def move_left_handler(self):
        self.move_left(5)

    @on_key("d", "held")
    def move_right_handler(self):
        self.move_right(5)

    @on_sprite_collision("Ball")
    def hit_ball(self):
        """React when touching the ball."""
        self.say("Ouch!", 1000)


class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self.set_background_color(50, 80, 130)
        self.add_child(Ball())
        self.add_child(Player())


# Create and run the game
game = Game(width=800, height=600, title="Scrawl Demo")
game.set_scene(MyScene())

print("[Scrawl Demo]")
print("Controls:")
print("  Arrow keys: Rotate the ball")
print("  WASD: Move the player")
print("  Space: Speed boost the ball")
print()

game.run(fps=60, debug=True)
