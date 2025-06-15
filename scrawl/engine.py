import pygame
import sys
import types
import math
import random
from collections import deque
from typing import Tuple, List, Callable, Any, Dict


# 添加装饰器定义
def as_main(func):
    """将函数标记为main函数，类似于原始的main方法"""
    func._is_main = True
    return func


def as_clones(func):
    """将函数标记为克隆体函数，类似于原始的clones方法"""
    func._is_clones = True
    return func


def handle_broadcast(event_name: str):
    """将函数标记为广播事件处理函数"""

    def decorator(func):
        func._broadcast_event = event_name
        return func

    return decorator


class Game:

    def __init__(self,
                 width: int = 800,
                 height: int = 600,
                 title: str = "Scratch-like Game",
                 font_path: str = "Simhei.ttf",
                 font_size: int = 20,
                 fullscreen: bool = False):
        pygame.init()
        self.width = width
        self.height = height
        self.title = title

        if fullscreen:
            self.screen = pygame.display.set_mode((width, height),
                                                  pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((width, height))

        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.scene = None
        self.running = False
        self.tasks = deque()
        self.current_time = 0
        
        # 创建中文字体 - 主要字体
        try:
            self.font = pygame.font.Font(font_path, font_size)
        except:
            # 无法加载指定字体时尝试使用系统默认字体
            print(f"警告: 无法加载字体 {font_path}, 将尝试使用系统字体")
            try:
                # 尝试常见中文字体
                fallback_fonts = ["simhei.ttf", "simsun.ttc", "DroidSansFallbackFull.ttf", 
                                 "msyh.ttc", "WenQuanYiMicroHei.ttf"]
                loaded = False
                for f in fallback_fonts:
                    try:
                        self.font = pygame.font.Font(f, font_size)
                        loaded = True
                        break
                    except:
                        continue

                if not loaded:
                    self.font = pygame.font.SysFont(None, font_size)
                    print("警告: 无法找到适合的中文字体, 使用系统默认字体")
            except:
                self.font = pygame.font.SysFont(None, font_size)
                print("警告: 字体初始化失败, 使用系统默认字体")

        # 创建调试字体 - 小一
        # self.debug_font = pygame.font.SysFont(None, debug_font_size)
        
        self.debug_info = []
        self.fps = 60
        self.background_color = (0, 0, 0)
        self.key_bindings = {}  # 全局按键绑定

    def run(self, fps: int = 60):
        if not self.scene:
            print("No scene set!")
            return

        self.fps = fps
        self.running = True

        self.scene.game = self
        self.scene.setup()

        while self.running:
            self.current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    # 先检查全局按键绑定
                    if event.key in self.key_bindings:
                        self.key_bindings[event.key]()
                    # 再检查场景按键绑定
                    elif self.scene and event.key in self.scene.key_bindings:
                        self.scene.key_bindings[event.key]()

                # 将事件传递给场景和精灵
                if self.scene:
                    self.scene.handle_event(event)
                    for sprite in self.scene.sprites:
                        sprite.handle_event(event)

            self.process_tasks()

            self.scene.pre_update()
            self.scene.update()
            for sprite in self.scene.sprites:
                sprite.update()
            self.scene.post_update()

            self.screen.fill(self.background_color)
            self.scene.draw(self.screen)
            self.draw_debug_info()

            pygame.display.flip()
            self.clock.tick(fps)

        pygame.quit()
        sys.exit()

    def set_background(self, color: Tuple[int, int, int]):
        self.background_color = color

    def bind_key(self, key: int, callback: Callable):
        """绑定全局按键"""
        self.key_bindings[key] = callback

    def unbind_all_keys(self):
        """清空全局按键绑定"""
        self.key_bindings = {}

    def set_scene(self, scene):
        """设置当前场景"""
        if self.scene:
            # 清除旧场景的按键绑定（但保留全局绑定）
            self.scene.unbind_all_keys()

        self.scene = scene
        scene.game = self
        scene.setup()
        self.log_debug(f"Switched to scene: {scene.name}")

    def add_task(self, generator, delay=0):
        self.tasks.append({
            'generator': generator,
            'next_run': self.current_time + delay
        })

    def process_tasks(self):
        if not self.tasks:
            return

        new_tasks = deque()
        while self.tasks:
            task = self.tasks.popleft()
            if self.current_time >= task['next_run']:
                try:
                    wait_time = next(task['generator'])
                    if wait_time is None:
                        wait_time = 0
                    task['next_run'] = self.current_time + wait_time
                    new_tasks.append(task)
                except StopIteration:
                    pass
                except TypeError:
                    pass
            else:
                new_tasks.append(task)

        self.tasks = new_tasks

    def log_debug(self, info: str):
        self.debug_info.append(info)

    def draw_debug_info(self):
        for i, info in enumerate(self.debug_info):
            text = self.font.render(info, True, (255, 255, 0))
            self.screen.blit(text, (10, 10 + i * 25))

        fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True,
                                    (255, 255, 0))
        self.screen.blit(fps_text, (self.width - 120, 10))

        if self.scene:
            sprite_count = f"Sprites: {len(self.scene.sprites)}"
            count_text = self.font.render(sprite_count, True, (255, 255, 0))
            self.screen.blit(count_text, (self.width - 120, 40))

            scene_name = f"Scene: {self.scene.name}"
            scene_text = self.font.render(scene_name, True, (255, 255, 0))
            self.screen.blit(scene_text, (self.width - 150, 70))

        self.debug_info = self.debug_info[-5:]


class Scene:

    def __init__(self):
        self.sprites: List[Sprite] = []
        self.background_color = (100, 150, 200)
        self.background_image: pygame.Surface = None
        self.game: Game = None
        self.name = "Scene"
        self.particle_systems: List[ParticleSystem] = []
        self.key_bindings = {}  # 场景特定的按键绑定

        self.main_tasks = []  # 存储所有标记为main的任务
        self.broadcast_handlers = {}  # 存储广播事件处理函数

    def setup(self):
        if not self.game:
            return

        self.game.log_debug(f"Scene '{self.name}' loaded")

        # 收集所有标记为@as_main的函数
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and hasattr(method, '_is_main'):
                self.main_tasks.append(method)

        # 收集所有标记为@handle_broadcast的函数
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and hasattr(method, '_broadcast_event'):
                event = getattr(method, '_broadcast_event')
                if event not in self.broadcast_handlers:
                    self.broadcast_handlers[event] = []
                self.broadcast_handlers[event].append(method)
        # 添加所有main任务到游戏队列
        for task in self.main_tasks:
            if hasattr(task, '__call__'):
                self.game.add_task(task())

        # 原有的main函数处理
        if hasattr(self, 'main') and callable(self.main):
            self.game.add_task(self.main())

        for sprite in self.sprites:
            sprite.setup(self)

    def add_sprite(self, sprite):
        self.sprites.append(sprite)
        if self.game:
            sprite.setup(self)
            self.game.log_debug(f"Added sprite: {sprite.name}")

    def add_particles(self, particle_system):
        self.particle_systems.append(particle_system)
        self.game.log_debug(f"Added particle system")

    def pre_update(self):
        for system in self.particle_systems:
            system.update()

    def post_update(self):
        self.sprites = [sprite for sprite in self.sprites if not sprite.delete]
        self.particle_systems = [
            sys for sys in self.particle_systems if not sys.finished
        ]

    def broadcast(self, event_name: str):
        if not self.game:
            return

        self.game.log_debug(f"Broadcasting event: {event_name}")

        # 优先调用匹配的装饰器处理函数
        for sprite in self.sprites:
            if event_name in sprite.broadcast_handlers:
                for handler in sprite.broadcast_handlers[event_name]:
                    self.game.add_task(handler())

        # 其次调用名为"on_{event_name}"的函数
        on_event_name = f"on_{event_name}"
        for sprite in self.sprites:
            if hasattr(sprite, on_event_name) and callable(
                    getattr(sprite, on_event_name)):
                self.game.add_task(getattr(sprite, on_event_name)())

        # 场景自身的事件处理
        if hasattr(self, on_event_name) and callable(
                getattr(self, on_event_name)):
            self.game.add_task(getattr(self, on_event_name)())

    def handle_event(self, event: pygame.event.Event):
        """处理场景特定的事件"""
        pass

    def bind_key(self, key: int, callback: Callable):
        """绑定场景特定的按键"""
        self.key_bindings[key] = callback

    def unbind_key(self, key: int):
        """解绑特定按键"""
        if key in self.key_bindings:
            del self.key_bindings[key]

    def unbind_all_keys(self):
        """清空场景按键绑定"""
        self.key_bindings = {}

    def update(self):
        """场景更新逻辑"""
        pass

    def draw(self, surface: pygame.Surface):
        if not self.game:
            return

        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(self.background_color)

        for sprite in self.sprites:
            if sprite.visible:
                sprite.draw(surface)

        for system in self.particle_systems:
            system.draw(surface)


class Sprite:

    def __init__(self):
        self.name = "Sprite"
        self.pos = pygame.Vector2(400, 300)
        self.direction = 90  # 默认方向：0=右，90=上
        self.size = 1.0
        self.visible = True
        self.delete = False
        self.scene: Scene = None
        self.game: Game = None

        # 图片管理相关属性
        self.costumes: Dict[str, pygame.Surface] = {}  # 存储所有造型的字典
        self.current_costume: str = None  # 当前使用的造型名称
        self._default_image: pygame.Surface = None  # 默认图像

        self.color = (255, 100, 100)
        self.speech: str = None
        self.speech_timer = 0
        self.pen_down = False
        self.pen_color = (0, 0, 0)
        self.pen_size = 2
        self.pen_path = []
        self.collision_radius = None
        self.main_tasks = []  # 存储所有标记为main的任务
        self.clones_tasks = []  # 存储所有标记为克隆任务的方法
        self.broadcast_handlers = {}  # 存储广播事件处理函数
        self.is_clones = False  # 标记是否为克隆体

    # 新增的图片管理方法
    def add_costume(self, name: str, image: pygame.Surface):
        """添加一个造型"""
        self.costumes[name] = image
        if not self._default_image:  # 如果没有默认图像，设为第一个添加的图像
            self._default_image = image

        # 添加：如果没有设置当前造型，设为第一个添加的造型
        if self.current_costume is None:
            self.current_costume = name

    def next_costume(self):
        """切换到下一个造型"""
        keys = list(self.costumes.keys())
        if len(keys) < 2:
            return

        current_index = keys.index(self.current_costume)
        next_index = (current_index + 1) % len(keys)
        self.switch_costume(keys[next_index])

    def switch_costume(self, name: str):
        """切换到指定名称的造型"""
        if name in self.costumes:
            self.current_costume = name
            self._update_collision_radius()

    def set_image(self, image: pygame.Surface):
        """设置当前使用的单个图像（向后兼容）"""
        self._default_image = image
        self._update_collision_radius()

    @property
    def image(self) -> pygame.Surface:
        """获取当前使用的图像"""
        # 优先返回当前造型的图像
        if self.current_costume and self.current_costume in self.costumes:
            return self.costumes[self.current_costume]

        # 如果没有造型，返回默认图像
        return self._default_image

    def _update_collision_radius(self):
        """根据当前图像更新碰撞半径"""
        image_to_use = None

        # 首先尝试获取当前造型
        if self.current_costume and self.current_costume in self.costumes:
            image_to_use = self.costumes[self.current_costume]
        # 如果当前造型不存在，尝试获取默认图像
        elif self._default_image:
            image_to_use = self._default_image
        # 如果都没有，使用默认的圆形大小
        else:
            self.collision_radius = 20 * self.size
            return

        # 更新基于图像的碰撞半径
        if self.image:
            w, h = self.image.get_size()
            self.collision_radius = min(w, h) // 2

    def main(self):
        pass

    def clones(self):
        pass

    def setup(self, scene: Scene):
        self.scene = scene
        self.game = scene.game

        # 更新碰撞半径
        self._update_collision_radius()

        if not self.game:
            return

        # 收集所有标记为@as_main的函数
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and hasattr(method, '_is_main'):
                self.main_tasks.append(method)

        # 收集所有标记为@as_clones的函数
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and hasattr(method, '_is_clones'):
                self.clones_tasks.append(method)

        # 收集所有标记为@handle_broadcast的函数
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and hasattr(method, '_broadcast_event'):
                event = getattr(method, '_broadcast_event')
                if event not in self.broadcast_handlers:
                    self.broadcast_handlers[event] = []
                self.broadcast_handlers[event].append(method)

        if not self.is_clones:
            # 添加所有main任务到游戏队列
            for task in self.main_tasks:
                if hasattr(task, '__call__'):
                    self.game.add_task(task())

            # 原有的main函数处理
            if hasattr(self, 'main') and callable(self.main):
                self.game.add_task(self.main())
        else:
            # 添加所有克隆任务到游戏队列
            for task in self.clones_tasks:
                if hasattr(task, '__call__'):
                    self.game.add_task(task())

            # 原有的克隆函数处理
            if hasattr(self, 'clones') and callable(self.clones):
                self.game.add_task(self.clones())

    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self):
        """基础精灵更新逻辑"""
        if not self.game:
            return

        # 更新说话气泡
        if self.speech and self.speech_timer > 0:
            self.speech_timer -= self.game.clock.get_time()
            if self.speech_timer <= 0:
                self.speech = None

    def broadcast(self, event_name: str):
        """广播事件，使所有精灵和场景都能响应"""
        #! 说不定要添加Game的广播方法
        if self.scene:
            self.scene.broadcast(event_name)

    def set_size(self, size: float):
        self.size = size
        self._update_collision_radius()

    def change_size(self, change_factor: float):
        self.size *= change_factor
        self._update_collision_radius()

    def move(self, steps: float):
        """移动精灵，无物理效果"""
        if not self.game:
            return

        rad = math.radians(self.direction)
        dx = steps * math.cos(rad)
        dy = -steps * math.sin(rad)
        self.pos.x += dx
        self.pos.y += dy

        # 确保不出边界
        radius = self.collision_radius
        if radius > 0:
            self.pos.x = max(radius, min(self.game.width - radius, self.pos.x))
            self.pos.y = max(radius, min(self.game.height - radius,
                                         self.pos.y))

        if self.pen_down:
            self.pen_path.append((int(self.pos.x), int(self.pos.y)))

    def turn_right(self, degrees: float):
        self.direction = (self.direction - degrees) % 360

    def turn_left(self, degrees: float):
        self.direction = (self.direction + degrees) % 360

    def point_in_direction(self, degrees: float):
        self.direction = degrees % 360

    def point_towards(self, x: float, y: float):
        dx = x - self.pos.x
        dy = y - self.pos.y
        self.direction = (90 - math.degrees(math.atan2(dy, dx))) % 360

    def goto(self, x: float, y: float):
        self.pos.x = x
        self.pos.y = y

    def goto_random_position(self):
        if not self.game:
            return

        radius = self.collision_radius
        self.pos.x = random.randint(radius, self.game.width - radius)
        self.pos.y = random.randint(radius, self.game.height - radius)

    def say(self, text: str, duration: int = 2000):
        self.speech = text
        self.speech_timer = duration

    def think(self, text: str, duration: int = 2000):
        self.say(text, duration)

    def change_color_to(self, color: Tuple[int, int, int]):
        self.color = color

    def change_color_random(self):
        self.color = (random.randint(0, 255), random.randint(0, 255),
                      random.randint(0, 255))

    def set_size(self, size: float):
        self.size = size
        if self.image:
            w, h = self.image.get_size()
            self.collision_radius = min(w, h) * size // 2

    def change_size(self, change_factor: float):
        self.size *= change_factor
        if self.image:
            w, h = self.image.get_size()
            self.collision_radius = min(w, h) * self.size // 2

    def clone(self):
        """克隆精灵"""
        if not self.game or not self.scene:
            return
        if len(self.scene.sprites) < 500:
            clone = self.__class__()
            clone.pos = pygame.Vector2(self.pos)
            clone.direction = self.direction
            clone.size = self.size
            clone.color = self.color

            # 确保克隆体复制所有造型
            clone.costumes = self.costumes.copy()  # 复制造型字典
            clone.current_costume = self.current_costume  # 保持当前造型

            # 复制图像属性
            clone._default_image = self._default_image
            clone.collision_radius = self.collision_radius

            clone.is_clones = True
            self.scene.add_sprite(clone)
            self.game.log_debug(f"Cloned sprite: {self.name}")

    def delete_self(self):
        self.delete = True

    # ------- 画笔控制 --------
    def pen_down(self):
        self.pen_down = True
        self.pen_path.append((int(self.pos.x), int(self.pos.y)))

    def pen_up(self):
        self.pen_down = False

    def change_pen_color(self, color: Tuple[int, int, int]):
        self.pen_color = color

    def set_pen_color_random(self):
        self.pen_color = (random.randint(0, 255), random.randint(0, 255),
                          random.randint(0, 255))

    def change_pen_size(self, size: int):
        self.pen_size = size

    def clear_pen(self):
        self.pen_path = []

    def draw(self, surface: pygame.Surface):
        """绘制精灵"""
        if not self.game or not self.visible:
            return
        # 绘制画笔轨迹
        if self.pen_down and len(self.pen_path) >= 2:
            pygame.draw.lines(surface, self.pen_color, False, self.pen_path,
                              self.pen_size)
        # 绘制精灵主体
        costume = self.image
        if costume:
            # 缩放图像
            if self.size != 1.0:
                orig_size = costume.get_size()
                new_size = (int(orig_size[0] * self.size),
                            int(orig_size[1] * self.size))
                scaled_costume = pygame.transform.scale(costume, new_size)
            else:
                scaled_costume = costume

            # 旋转图像
            rotated_image = pygame.transform.rotate(scaled_costume,
                                                    self.direction - 90)
            rect = rotated_image.get_rect(center=self.pos)
            surface.blit(rotated_image, rect)
        else:
            # 没有图像时绘制圆形
            radius = int(self.collision_radius * self.size)
            pygame.draw.circle(surface, self.color,
                               (int(self.pos.x), int(self.pos.y)), radius)
            end_x = self.pos.x + radius * math.cos(math.radians(
                self.direction))
            end_y = self.pos.y - radius * math.sin(math.radians(
                self.direction))
            pygame.draw.line(surface, (0, 0, 0), self.pos, (end_x, end_y), 2)

        # 绘制说话气泡
        if self.speech:
            text = self.game.font.render(self.speech, True, (0, 0, 0))
            bubble_rect = pygame.Rect(0, 0,
                                      text.get_width() + 20,
                                      text.get_height() + 15)
            bubble_rect.center = (self.pos.x, self.pos.y - 50)

            pygame.draw.rect(surface, (255, 255, 200),
                             bubble_rect,
                             border_radius=10)
            pygame.draw.rect(surface, (200, 200, 100),
                             bubble_rect,
                             2,
                             border_radius=10)

            points = [(bubble_rect.centerx, bubble_rect.bottom),
                      (bubble_rect.centerx - 10, bubble_rect.bottom + 10),
                      (bubble_rect.centerx + 10, bubble_rect.bottom + 10)]
            pygame.draw.polygon(surface, (255, 255, 200), points)
            pygame.draw.polygon(surface, (200, 200, 100), points, 2)

            surface.blit(text, (bubble_rect.x + 10, bubble_rect.y + 7))



class Cat(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Cat"
        
        self.add_costume(
            "costume1", 
            pygame.image.load("cat1.svg").convert_alpha()
        )
        self.add_costume(
            "costume2", 
            pygame.image.load("cat2.svg").convert_alpha()
        )
        
    def walk(self):
        self.next_costume()


class Particle:
    """单个粒子"""

    def __init__(self, x, y, velocity, color, size, life):
        self.pos = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(velocity)
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = pygame.Vector2(0, 0.1)

    def update(self):
        self.pos += self.velocity
        self.velocity += self.gravity
        self.life -= 15

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            if alpha < 0:
                alpha = 0

            r, g, b = self.color
            color = (r, g, b, alpha)

            particle_surf = pygame.Surface((self.size * 2, self.size * 2),
                                           pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color, (self.size, self.size),
                               self.size)
            surface.blit(particle_surf,
                         (self.pos.x - self.size, self.pos.y - self.size))


class ParticleSystem:
    """粒子系统"""

    def __init__(self, x, y, count=50, life_range=(500, 1500)):
        self.particles = []
        self.x = x
        self.y = y
        self.count = count
        self.life_range = life_range
        self.finished = False
        self._create_particles()

    def _create_particles(self):
        for _ in range(self.count):
            angle = random.uniform(0, 360)
            speed = random.uniform(1, 5)
            rad = math.radians(angle)
            velocity = pygame.Vector2(
                math.cos(rad) * speed, -math.sin(rad) * speed)

            color = (random.randint(200, 255), random.randint(100, 255),
                     random.randint(50, 150))

            size = random.randint(2, 6)
            life = random.randint(self.life_range[0], self.life_range[1])

            self.particles.append(
                Particle(self.x, self.y, velocity, color, size, life))

    def update(self):
        active_count = 0
        for particle in self.particles:
            if particle.life > 0:
                particle.update()
                active_count += 1

        self.finished = (active_count == 0)

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)


class PhysicsSprite(Sprite):
    """添加物理属性的精灵类"""

    def __init__(self):
        super().__init__()
        # 物理属性
        self.velocity = pygame.Vector2(0, 0)  # 速度向量
        self.angular_velocity = 0  # 角速度（度/帧）
        self.friction = 0.98  # 摩擦力系数
        self.gravity = pygame.Vector2(0, 0.2)  # 重力向量
        self.elasticity = 0.8  # 弹性系数

    def update(self):
        """物理精灵更新逻辑：处理物理模拟"""
        super().update()  # 调用基类的更新方法处理公共逻辑

        # 应用物理效果
        self.apply_physics()

        # 检查边界碰撞
        if self.collision_radius > 0:
            self.check_boundaries()

    def apply_physics(self):
        """应用物理效果 - 速度和加速度"""
        # 应用重力
        self.velocity += self.gravity

        # 应用摩擦力
        self.velocity *= self.friction

        # 应用角速度
        self.direction = (self.direction + self.angular_velocity) % 360

        # 更新位置
        self.pos += self.velocity

        # 记录画笔轨迹
        if self.pen_down:
            self.pen_path.append((int(self.pos.x), int(self.pos.y)))

    def check_boundaries(self):
        """检查边界碰撞"""
        radius = self.collision_radius

        # 左边界
        if self.pos.x < radius:
            self.pos.x = radius
            if self.velocity.x < 0:
                self.velocity.x = -self.velocity.x * self.elasticity
            self.on_boundary_hit("left")

        # 右边界
        if self.pos.x > self.game.width - radius:
            self.pos.x = self.game.width - radius
            if self.velocity.x > 0:
                self.velocity.x = -self.velocity.x * self.elasticity
            self.on_boundary_hit("right")

        # 上边界
        if self.pos.y < radius:
            self.pos.y = radius
            if self.velocity.y < 0:
                self.velocity.y = -self.velocity.y * self.elasticity
            self.on_boundary_hit("top")

        # 下边界
        if self.pos.y > self.game.height - radius:
            self.pos.y = self.game.height - radius
            if self.velocity.y > 0:
                self.velocity.y = -self.velocity.y * self.elasticity
            self.on_boundary_hit("bottom")

    def on_boundary_hit(self, boundary: str):
        """边界碰撞回调 - 可被子类重写"""
        pass

    # ------- 物理控制方法 -------
    def apply_force(self, force_x: float, force_y: float):
        """应用力改变速度"""
        self.velocity.x += force_x
        self.velocity.y += force_y

    def apply_impulse(self, impulse_x: float, impulse_y: float):
        """应用冲量（立即改变速度）"""
        self.velocity.x += impulse_x
        self.velocity.y += impulse_y

    def set_velocity(self, velocity_x: float, velocity_y: float):
        """设置速度矢量"""
        self.velocity = pygame.Vector2(velocity_x, velocity_y)

    def set_gravity(self, gravity_x: float, gravity_y: float):
        """设置重力"""
        self.gravity = pygame.Vector2(gravity_x, gravity_y)

    def set_elasticity(self, elasticity: float):
        """设置弹性系数（0-1之间）"""
        self.elasticity = min(max(elasticity, 0), 1.0)

    def set_friction(self, friction: float):
        """设置摩擦力系数（0-1之间）"""
        self.friction = min(max(friction, 0), 1.0)

    def set_rotation(self, degrees_per_frame: float):
        """设置旋转速度（度/帧）"""
        self.angular_velocity = degrees_per_frame

    # ------- 绘制额外物理信息 -------
    def draw(self, surface: pygame.Surface):
        """绘制精灵及物理信息"""
        super().draw(surface)  # 绘制基类内容

        # 额外绘制物理信息
        if not self.visible or not self.game:
            return

        # 计算碰撞半径
        radius = int(self.collision_radius * self.size)

        # 绘制速度矢量
        if self.velocity.length() > 0:
            end_vx = self.pos.x + self.velocity.x * 10
            end_vy = self.pos.y + self.velocity.y * 10
            pygame.draw.line(surface, (255, 0, 0), self.pos, (end_vx, end_vy),
                             2)

            # 在箭头处绘制速度值
            speed = self.velocity.length()
            speed_text = f"{speed:.1f}"
            speed_surf = self.game.font.render(speed_text, True, (255, 0, 0))
            surface.blit(speed_surf, (end_vx + 5, end_vy - 10))
