"""
Scrawl v2 Minimal Test - Verify coroutine execution + input

Prints position changes to confirm the engine loop is working.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python"))
from scrawl_v2 import *


class Ball(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Ball"
        self.x = 400.0
        self.y = 300.0
        self.direction = 45.0
        self._frame = 0

    @as_main
    def main_loop(self):
        while True:
            self.move(3)
            self._frame += 1
            if self._frame % 60 == 0:
                print(f"  Ball at ({self.x:.1f}, {self.y:.1f}) frame={self._frame}")
            yield 16

    @on_key("space", "pressed")
    def on_space(self):
        print("  SPACE pressed!")
        self.x = 400.0
        self.y = 300.0

    @on_key("left", "held")
    def on_left(self):
        self.turn_left(5)

    @on_key("right", "held")
    def on_right(self):
        self.turn_right(5)


class TestScene(Scene):
    def __init__(self):
        super().__init__()
        self.set_background_color(20, 20, 40)
        self.add_sprite(Ball())


game = Game(width=800, height=600, title="Scrawl v2 - Coroutine Test")
game.set_scene(TestScene())
print("[Test] Starting... watch for position updates every 60 frames")
print("[Test] Press SPACE to reset ball, LEFT/RIGHT to rotate, close window to exit")
game.run()
print("[Test] Done!")
