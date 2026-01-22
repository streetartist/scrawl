from scrawl import *
import pygame
import time

# svg files from https://scratch.mit.edu/projects/239626199/editor/
# 游戏说明：
# 通过左右方向键控制女巫旋转；
# 通过空格键控制火球发射（点一次发射一个）；
# 碰到敌人就Game Over；
# 按a键使用屏障，屏障显示3秒，10秒可用一次。

LIFE = 3  # 初始生命数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCORE = 0  # 初始分数

# 创建游戏实例
game = Game()


class Bat1(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "Bat1"

        self.add_costume("costume1",
                         pygame.image.load("bat1-b.svg").convert_alpha())
        self.add_costume("costume2",
                         pygame.image.load("bat1-a.svg").convert_alpha())
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
            self.move(8) # 快速蝙蝠
            yield 200

    @as_main
    def main1(self):
        while True:
            yield 3000
            # 添加蝙蝠
            self.clone()

    @handle_sprite_collision("FireBall")
    def killed(self, other):
        self.delete_self()
        self.broadcast("add_score")

    @handle_sprite_collision("Wall")
    def die(self, other):
        self.delete_self()

    @handle_sprite_collision("Witch")
    def hit_witch(self, other):
        self.delete_self()

class Bat2(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "Bat2"

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

    @handle_sprite_collision("Witch")
    def hit_witch(self, other):
        self.delete_self()
        
    @handle_sprite_collision("FireBall")
    def killed(self, other):
        self.delete_self()
        self.broadcast("add_score")

    @handle_sprite_collision("Wall")
    def die(self, other):
        self.delete_self()

class Dragon(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "Dragon"

        self.add_costume("costume1",
                         pygame.image.load("dragon1-a.svg").convert_alpha())
        self.add_costume("costume2",
                         pygame.image.load("dragon1-b.svg").convert_alpha())
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
            self.face_towards("Witch")
            self.turn_right(80)
            self.move(20)
            yield 200

    @as_main
    def main1(self):
        while True:
            yield 3000
            # 添加龙
            self.clone()

    @handle_sprite_collision("FireBall")
    def killed(self, other):
        self.delete_self()
        self.broadcast("add_score")

    @handle_sprite_collision("Witch")
    def hit_witch(self, other):
        self.delete_self()

class Hippo(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "Hippo"

        self.add_costume("costume1",
                         pygame.image.load("hippo1-a.svg").convert_alpha())
        self.add_costume("costume2",
                         pygame.image.load("hippo1-b.svg").convert_alpha())
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
            # 添加河马
            self.clone()

    @handle_sprite_collision("Witch")
    def hit_witch(self, other):
        self.delete_self()

    @handle_sprite_collision("Wall")
    def die(self, other):
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
        self.delete_self()

class Wall(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Wall"
        self.add_costume("costume1",
                         pygame.image.load("wall.png").convert_alpha())
        self.set_size(0.5)
        self.last_use = time.time() # 记录上一次使用
        self.visible = False

    @on_key(pygame.K_a, "pressed")
    def use_wall(self):
        if time.time() - self.last_use >= 10: # 最多10秒用一次屏障
            self.visible = True
            yield 3000 # 屏障显示3秒
            self.visible = False
            self.last_use = time.time()
            

class Gameover(Sprite):
    def __init__(self):
        super().__init__()
        self.add_costume("costume1",
                         pygame.image.load("gameover.png").convert_alpha())
        self.visible = False

    @handle_broadcast("gameover")
    def gameover(self):
        self.visible = True

class Witch(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "Witch"

        self.add_costume("costume1",
                         pygame.image.load("witch.svg").convert_alpha())

        self.fireball = FireBall()
        self.set_size(0.7)

    @on_key(pygame.K_RIGHT, "held")
    def right_held(self):
        self.turn_right(2)

    @on_key(pygame.K_LEFT, "held")
    def left_held(self):
        self.turn_left(2)

    @on_key(pygame.K_SPACE, "pressed")
    def space_pressed(self):
        self.fireball.direction = self.direction
        self.clone(self.fireball)

    @handle_sprite_collision("Bat1")
    @handle_sprite_collision("Bat2")
    @handle_sprite_collision("Dragon")
    def reduce_life(self):
        self.broadcast("reduce_life")

    @handle_sprite_collision("Hippo")
    def add_life(self):
        self.broadcast("add_life")

# 剩余生命数显示精灵
class Life(Sprite):
    def __init__(self, bird):
        super().__init__()
        self.name = "life"
        
        self.font = pygame.font.SysFont(None, 28)
        
        # 初始生命数显示
        self.update_display()
        
        # 设置精灵位置 (居中靠上)
        self.pos.x = SCREEN_WIDTH // 2
        self.pos.y = 40
    
    def update_display(self):
        """更新生命数显示"""
        # 渲染生命数文本
        score_text = f"剩余生命：{LIFE}"
        text_surface = self.font.render(score_text, True, (255, 255, 255))
        
        # 添加阴影效果
        shadow_surface = self.font.render(score_text, True, (0, 0, 0))
        
        # 创建最终表面（稍大一点以容纳阴影）
        self.surface = pygame.Surface((text_surface.get_width() + 4, text_surface.get_height() + 4), pygame.SRCALPHA)
        
        # 绘制阴影（偏移2像素）
        self.surface.blit(shadow_surface, (2, 2))
        # 绘制主文本
        self.surface.blit(text_surface, (0, 0))
        
        # 设置精灵造型
        self.add_costume("default", self.surface)
    
    @handle_broadcast("reduce_life")
    def reduce_life(self):
        """减少生命数+显示"""
        global LIFE
        LIFE -= 1
        if LIFE <= 0:
            self.broadcast("gameover")
        else:    
            self.update_display()
    
    @handle_broadcast("add_life")
    def add_life(self):
        """增加生命数+显示"""
        global LIFE
        LIFE += 1
        self.update_display()


# 得分显示精灵
class Score(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "score"
        
        self.font = pygame.font.SysFont(None, 24) # 字体稍小
        
        self.update_display()
        
        # 设置位置，在生命数下方
        self.pos.x = SCREEN_WIDTH // 2
        self.pos.y = 70
    
    def update_display(self):
        """更新当前得分显示"""
        score_text = f"得分: {SCORE}"
        text_surface = self.font.render(score_text, True, (255, 255, 255))
        shadow_surface = self.font.render(score_text, True, (0, 0, 0))
        
        self.surface = pygame.Surface((text_surface.get_width() + 4, text_surface.get_height() + 4), pygame.SRCALPHA)
        self.surface.blit(shadow_surface, (2, 2))
        self.surface.blit(text_surface, (0, 0))
        
        self.add_costume("default", self.surface)
    
    @handle_broadcast("add_score")
    def add_score(self):
        """增加得分+显示"""
        global SCORE
        SCORE += 10
        self.update_display()
    

# 定义场景
class MyScene(Scene):

    def __init__(self):
        super().__init__()

        bat1 = Bat1()
        self.add_sprite(bat1)

        bat2 = Bat2()
        self.add_sprite(bat2)

        dragon = Dragon()
        self.add_sprite(dragon)

        hippo = Hippo()
        self.add_sprite(hippo)

        witch = Witch()
        self.add_sprite(witch)

        wall = Wall()
        self.add_sprite(wall)

        gameover = Gameover()
        self.add_sprite(gameover)

        life_display = Life(witch)
        self.add_sprite(life_display)

        score_display = Score()
        self.add_sprite(score_display)

# 运行游戏
game.set_scene(MyScene())
game.run(fps=60)
