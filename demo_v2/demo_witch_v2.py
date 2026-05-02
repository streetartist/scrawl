"""
Scrawl v2 port of the Witch demo.
Original: demo_project/scrawl_demo_witch-main-main/demo.py
"""

import os
import time

from scrawl import *

# Asset directory (relative to this script)
ASSET_DIR = os.path.dirname(os.path.abspath(__file__))

def asset(name):
    return os.path.join(ASSET_DIR, name)

LIFE = 3
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCORE = 0


class Bat1(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Bat1"
        self.add_costume("costume1", asset("bat1-b.svg"))
        self.add_costume("costume2", asset("bat1-a.svg"))
        self.visible = False
        self.set_size(0.5)

    @as_clones
    def clones1(self):
        self.pos = (400, 300)
        self.face_random_direction()
        self.move(400)
        self.face_towards("Witch")
        self.visible = True
        while True:
            self.next_costume()
            yield 300

    @as_clones
    def clones2(self):
        while True:
            self.move(8)
            yield 200

    @as_main
    def main1(self):
        while True:
            yield 3000
            self.clone()

    @on_sprite_collision("FireBall")
    def killed(self):
        self.delete_self()
        self.broadcast("add_score")

    @on_sprite_collision("Wall")
    def die(self):
        self.delete_self()

    @on_sprite_collision("Witch")
    def hit_witch(self):
        self.delete_self()


class Dragon(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Dragon"
        self.add_costume("costume1", asset("dragon1-a.svg"))
        self.add_costume("costume2", asset("dragon1-b.svg"))
        self.visible = False
        self.set_size(0.5)

    @as_clones
    def clones1(self):
        self.pos = (400, 300)
        self.face_random_direction()
        self.move(400)
        self.face_towards("Witch")
        self.visible = True
        while True:
            self.next_costume()
            yield 300

    @as_clones
    def clones2(self):
        while True:
            self.face_towards("Witch")
            self.turn_right(80)
            self.move(20)
            yield 200

    @as_main
    def main1(self):
        while True:
            yield 3000
            self.clone()

    @on_sprite_collision("FireBall")
    def killed(self):
        self.delete_self()
        self.broadcast("add_score")

    @on_sprite_collision("Witch")
    def hit_witch(self):
        self.delete_self()


class Hippo(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Hippo"
        self.add_costume("costume1", asset("hippo1-a.svg"))
        self.add_costume("costume2", asset("hippo1-b.svg"))
        self.visible = False
        self.set_size(0.5)

    @as_clones
    def clones1(self):
        self.pos = (400, 300)
        self.face_random_direction()
        self.move(400)
        self.face_towards("Witch")
        self.visible = True
        while True:
            self.next_costume()
            yield 300

    @as_clones
    def clones2(self):
        while True:
            self.move(5)
            yield 200

    @as_main
    def main1(self):
        while True:
            yield 3000
            self.clone()

    @on_sprite_collision("FireBall")
    def killed(self):
        self.delete_self()
        self.broadcast("add_score")

    @on_sprite_collision("Witch")
    def hit_witch(self):
        self.delete_self()

    @on_sprite_collision("Wall")
    def die(self):
        self.delete_self()


class FireBall(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "FireBall"
        self.add_costume("costume1", asset("ball-a.svg"))
        self.visible = False
        self.set_size(0.2)

    @as_clones
    def clones1(self):
        self.visible = True
        while True:
            self.move(10)
            yield 100

    @on_edge_collision()
    def finish(self):
        self.delete_self()


class Wall(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Wall"
        self.add_costume("costume1", asset("wall.png"))
        self.set_size(0.5)
        self.last_use = time.time()
        self.visible = False

    @on_key("a", "pressed")
    def use_wall(self):
        if time.time() - self.last_use >= 10:
            self.visible = True
            yield 3000
            self.visible = False
            self.last_use = time.time()


class Gameover(Sprite):
    def __init__(self):
        super().__init__()
        self.add_costume("costume1", asset("gameover.png"))
        self.visible = False

    @on_broadcast("gameover")
    def gameover(self):
        self.visible = True


class Witch(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Witch"
        self.add_costume("costume1", asset("witch.svg"))
        self.fireball = FireBall()
        self.set_size(0.7)

    @on_key("right", "held")
    def right_held(self):
        self.turn_right(2)

    @on_key("left", "held")
    def left_held(self):
        self.turn_left(2)

    @on_key("space", "held")
    def space_pressed(self):
        self.fireball.direction = self.direction
        self.clone(self.fireball)

    @on_sprite_collision("Bat1")
    @on_sprite_collision("Bat2")
    @on_sprite_collision("Dragon")
    def reduce_life(self):
        self.broadcast("reduce_life")

    @on_sprite_collision("Hippo")
    def add_life(self):
        self.broadcast("add_life")


class LifeDisplay(Sprite):
    """Displays life count on screen."""
    def __init__(self):
        super().__init__()
        self.name = "LifeDisplay"
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 30
        self.visible = False
        self.life = LIFE

    @as_main
    def init_text(self):
        self.set_text(f"Life: {self.life}", 24, (255, 255, 255))
        yield 0

    @on_broadcast("reduce_life")
    def on_reduce(self):
        self.life -= 1
        self.set_text(f"Life: {self.life}", 24, (255, 100, 100) if self.life <= 1 else (255, 255, 255))
        if self.life <= 0:
            self.broadcast("gameover")

    @on_broadcast("add_life")
    def on_add(self):
        self.life += 1
        self.set_text(f"Life: {self.life}", 24, (255, 255, 255))


class ScoreDisplay(Sprite):
    """Displays score on screen."""
    def __init__(self):
        super().__init__()
        self.name = "ScoreDisplay"
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 60
        self.visible = False
        self.score = 0

    @as_main
    def init_text(self):
        self.set_text(f"Score: {self.score}", 20, (255, 255, 100))
        yield 0

    @on_broadcast("add_score")
    def on_score(self):
        self.score += 10
        self.set_text(f"Score: {self.score}", 20, (255, 255, 100))


class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self.set_background_color(20, 20, 40)
        self.add_sprite(Bat1())
        self.add_sprite(Dragon())
        self.add_sprite(Hippo())
        self.add_sprite(Witch())
        self.add_sprite(Wall())
        self.add_sprite(Gameover())
        self.add_sprite(FireBall())
        self.add_sprite(LifeDisplay())
        self.add_sprite(ScoreDisplay())


# Run
print("[Witch Demo v2]")
print("Controls: LEFT/RIGHT=rotate, SPACE=fire, A=shield")
print()
game = Game(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Witch - Scrawl v2")
game.set_scene(MyScene())
game.run(fps=120, debug=False)
