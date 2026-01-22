from scrawl import *
import pygame

# svg files from https://scratch.mit.edu/projects/239626199/editor/

# 创建游戏实例
game = Game()


class Bat(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "Bat"

        self.add_costume("costume1",
                         pygame.image.load("bat2-b.svg").convert_alpha())
        self.add_costume("costume2",
                         pygame.image.load("bat2-a.svg").convert_alpha())
        self.visible = False
        self.set_size(0.5)

    @as_clones
    def clones1(self):
        self.pos = pygame.Vector2(400, 300)
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
            # 添加蝙蝠
            self.clone()

    @handle_edge_collision()
    def finish(self):
        # print("触发边缘删除!")
        self.delete_self()

    @handle_sprite_collision("FireBall")
    def hit_fireball(self, other):
        # print("触发精灵删除!")
        self.delete_self()

    @handle_sprite_collision("Witch")
    def hit_witch(self, other):
        # print("触发精灵删除!")
        self.delete_self()


class FireBall(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "FireBall"
        self.add_costume("costume1",
                         pygame.image.load("ball-a.svg").convert_alpha())
        self.visible = False
        self.set_size(0.2)

    @as_clones
    def clones1(self):
        self.visible = True

        while True:
            self.move(10)
            yield 100

    @handle_edge_collision()
    def finish(self):
        #print("触发边缘删除!")
        self.delete_self()


class Witch(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "Witch"

        self.add_costume("costume1",
                         pygame.image.load("witch.svg").convert_alpha())

        self.fireball = FireBall()

    @on_key(pygame.K_s, "held")
    def right_held(self):
        self.turn_right(2)

    @on_key(pygame.K_d, "held")
    def left_held(self):
        self.turn_left(2)

    @on_key(pygame.K_SPACE, "held")
    def space_pressed(self):
        self.fireball.direction = self.direction
        self.clone(self.fireball)

    def main(self):
        print("witch main")


# 定义场景
class MyScene(Scene):

    def __init__(self):
        super().__init__()

        bat = Bat()
        self.add_sprite(bat)

        witch = Witch()
        self.add_sprite(witch)


# 运行游戏
game.set_scene(MyScene())
game.run(fps=60)
