import pygame
from pygame import K_SPACE
import random
from scrawl import Game, Scene, PhysicsSprite, Sprite, on_key, as_main, on_mouse_event, handle_edge_collision, handle_sprite_collision, CloudVariablesClient
import time

# 游戏常量
SCREEN_WIDTH = 288
SCREEN_HEIGHT = 512
GRAVITY = 0.5
FLAP_FORCE = -7
PIPE_SPEED = 2.5
PIPE_GAP = 120
PIPE_FREQUENCY = 1500  # 每1500ms生成一个新管道

client = CloudVariablesClient(project_id="0a668321-a7f0-4663-8d68-27c515142875")

class Bird(PhysicsSprite):
    def __init__(self):
        super().__init__()
        self.name = "小鸟"
        self.set_collision_type("mask")
        
        # 创建小鸟图像
        bird_width = 24
        bird_height = 17
        surface = pygame.Surface((bird_width, bird_height), pygame.SRCALPHA)
        pygame.draw.ellipse(surface, (255, 200, 0), (0, 0, bird_width, bird_height))  # 鸟身体
        pygame.draw.circle(surface, (255, 100, 0), (bird_width - 9, 6), 3)  # 鸟头
        pygame.draw.polygon(surface, (255, 0, 0), [
            (bird_width - 6, 6), 
            (bird_width + 4, 6), 
            (bird_width - 1, 8)
        ])  # 鸟嘴
        pygame.draw.ellipse(surface, (0, 0, 0), (bird_width - 12, 4, 3, 3))  # 眼睛
        
        self.add_costume("default", surface)
        self.pos.x = SCREEN_WIDTH // 3  # 初始位置在屏幕1/3处
        self.pos.y = SCREEN_HEIGHT // 2
        
        # 设置物理属性
        self.set_gravity(0, GRAVITY)
        self.set_elasticity(0.2)
        self.set_friction(0.99)
        
        # 游戏状态
        self.game_over = False
        self.score = 0
    
    @on_key(K_SPACE, "pressed")
    @on_mouse_event(button=1, mode="pressed")
    def flap(self):
        """按下空格键或鼠标使小鸟上升"""
        if not self.game_over:
            self.velocity.y = FLAP_FORCE
            self.play_sound("flap")  # 播放拍翅膀音效
    
    @handle_edge_collision("top")
    def hit_top(self):
        """碰到上边界"""
        if not self.game_over:
            self.velocity.y = 0
            self.pos.y = 10
    
    @handle_edge_collision("bottom")
    @handle_sprite_collision("管道")
    def hit_bottom(self):
        """碰到下边界或管道 - 游戏结束"""
        if not self.game_over:
            self.game.log_debug("!!!!!")
            self.game_over = True
            self.say("Ouch!", 3000)
            self.play_sound("hit")  # 播放撞击音效
            
            # 从云变量中获取当前最高分，如果不存在则默认为0
            current_highest = client.get_variable("highest_score", 0)
            
            # 如果当前分数高于最高分，则更新云变量
            if self.score > current_highest:
                client.set_variable("highest_score", self.score)
    
    @as_main
    def bird_physics(self):
        """处理小鸟物理状态"""
        while True:
            # 旋转小鸟基于下落速度
            self.direction = max(-30, min(self.velocity.y * 2, 90))
            yield 0

class Pipe(Sprite):
    def __init__(self, x, gap_y):
        super().__init__()
        
        self.name = "管道"
        self.set_collision_type("mask")
        
        # 随机管道高度
        top_height = gap_y - PIPE_GAP // 2
        bottom_height = SCREEN_HEIGHT - (gap_y + PIPE_GAP // 2)
        
        # 管道宽度
        pipe_width = 52 * (SCREEN_WIDTH / 400)
        
        # 直接在一个surface上绘制管道
        surface = pygame.Surface((pipe_width, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # 绘制上管道（从顶部向下绘制）
        pygame.draw.rect(surface, (0, 180, 0), (0, 0, pipe_width, top_height))
        # 上管道顶部装饰
        pygame.draw.rect(surface, (0, 140, 0), (0, top_height - 15, pipe_width, 15))
        
        # 绘制下管道（从间隙底部开始绘制）
        bottom_pipe_y = gap_y + PIPE_GAP // 2
        pygame.draw.rect(surface, (0, 180, 0), (0, bottom_pipe_y, pipe_width, bottom_height))
        # 下管道顶部装饰
        pygame.draw.rect(surface, (0, 140, 0), (0, bottom_pipe_y, pipe_width, 15))
        
        self.add_costume("default", surface)
        self.collision_mask = pygame.mask.from_surface(self.image)
        self.pos.x = x
        self.pos.y = SCREEN_HEIGHT // 2
        
        # 管道属性
        self.passed = False  # 小鸟是否已通过该管道
    
    @as_main
    def move_pipe(self):
        """移动管道"""
        while True:
            if not self.scene.bird.game_over:
                self.pos.x -= PIPE_SPEED
                
                # 检测小鸟是否通过管道
                if not self.passed and self.pos.x < self.scene.bird.pos.x:
                    self.passed = True
                    self.scene.bird.score += 1
                    self.play_sound("point")  # 播放得分音效
                
                # 管道移出屏幕后删除
                if self.pos.x < -100:
                    self.delete_self()
            
            yield 0

class Ground(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "地面"
        
        # 创建地面图像
        ground_height = 40
        surface = pygame.Surface((SCREEN_WIDTH, ground_height))
        surface.fill((222, 184, 135))  # 浅棕色地面
        
        # 添加草地纹理
        pygame.draw.rect(surface, (0, 180, 0), (0, 0, SCREEN_WIDTH, 8))
        for i in range(0, SCREEN_WIDTH, 15):
            pygame.draw.line(surface, (0, 140, 0), (i, 8), (i+8, 8), 2)
        
        self.add_costume("default", surface)
        self.pos.x = SCREEN_WIDTH // 2
        self.pos.y = SCREEN_HEIGHT - ground_height // 2

class ScoreSprite(Sprite):
    def __init__(self, bird):
        super().__init__()
        self.name = "得分显示"
        self.bird = bird  # 引用小鸟对象以获取分数
        
        self.font = pygame.font.SysFont(None, 28)
        
        # 初始分数显示
        self.update_score()
        
        # 设置精灵位置 (居中靠上)
        self.pos.x = SCREEN_WIDTH // 2
        self.pos.y = 40
    
    def update_score(self):
        """更新分数显示"""
        # 渲染分数文本
        score_text = f"Score: {self.bird.score}"
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
    
    @as_main
    def update_loop(self):
        """持续更新分数显示"""
        last_score = -1  # 初始值确保第一次会更新
        while True:
            # 当分数变化时更新显示
            if self.bird.score != last_score:
                self.update_score()
                last_score = self.bird.score
            yield 0
            
# 最高分显示精灵
class HighestScoreDisplay(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "最高分显示"
        
        self.font = pygame.font.SysFont(None, 24) # 字体稍小
        
        self.highest_score = 0
        self.update_display()
        
        # 设置位置，在当前分数下方
        self.pos.x = SCREEN_WIDTH // 2
        self.pos.y = 70
    
    def update_display(self):
        """更新最高分显示"""
        self.highest_score = client.get_variable("highest_score", 0) # 从云端获取，默认为0
        
        score_text = f"Highest: {self.highest_score}"
        text_surface = self.font.render(score_text, True, (255, 255, 255))
        shadow_surface = self.font.render(score_text, True, (0, 0, 0))
        
        self.surface = pygame.Surface((text_surface.get_width() + 4, text_surface.get_height() + 4), pygame.SRCALPHA)
        self.surface.blit(shadow_surface, (2, 2))
        self.surface.blit(text_surface, (0, 0))
        
        self.add_costume("default", self.surface)
    
    @as_main
    def update_loop(self):
        """持续更新最高分显示"""
        last_highest_score = -1
        while True:
            current_highest = client.get_variable("highest_score", 0)
            if current_highest != last_highest_score:
                self.update_display()
                last_highest_score = current_highest
            # 每0.1秒更新一次最高分
            yield 100

class FlappyScene(Scene):
    def __init__(self):
        super().__init__()
        self.name = "Flappy Bird"
        self.background_color = (135, 206, 235)  # 天蓝色背景
        
        # 添加云朵装饰
        for _ in range(4):
            cloud = Sprite()
            cloud_size = random.randint(20, 50)
            surface = pygame.Surface((cloud_size*2, cloud_size), pygame.SRCALPHA)
            pygame.draw.ellipse(surface, (255, 255, 255), (0, 0, cloud_size*2, cloud_size))
            cloud.add_costume("default", surface)
            cloud.pos.x = random.randint(0, SCREEN_WIDTH)
            cloud.pos.y = random.randint(40, 150)  # 降低云朵高度
            self.add_sprite(cloud)
        
        # 添加游戏元素
        self.bird = Bird()
        self.add_sprite(self.bird)
        
        self.ground = Ground()
        self.add_sprite(self.ground)
        
        # 添加得分显示精灵
        self.score_display = ScoreSprite(self.bird)
        self.add_sprite(self.score_display)

        # 添加最高分显示精灵
        self.highest_score_display = HighestScoreDisplay()
        self.add_sprite(self.highest_score_display)
    
    @as_main
    def generate_pipes(self):
        # 加载音效
        self.game.load_sound("flap", "sounds/flap.ogg")
        self.game.load_sound("hit", "sounds/hit.ogg")
        self.game.load_sound("point", "sounds/point.ogg")
        
        """定时生成新管道"""
        while True:
            if not self.bird.game_over:
                # 随机管道位置 (确保间隙在屏幕内)
                gap_y = random.randint(120, SCREEN_HEIGHT - 120)
                new_pipe = Pipe(SCREEN_WIDTH + 30, gap_y)
                self.add_sprite(new_pipe)
            
            yield PIPE_FREQUENCY  # 等待一段时间后生成新管道
            
time.sleep(2)

# 创建并运行游戏
game = Game(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="Flappy Bird - Scrawl 复刻版", fullscreen=True)
game.set_scene(FlappyScene())
game.run(fps=60)