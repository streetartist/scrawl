import pygame
import sys
import types
import math
import random
from collections import deque
from typing import Tuple, List, Callable, Any, Dict, Optional
import os

import requests
import time
import threading
import uuid
import json
import traceback

# 配置信息 - 替换为您的实际值
SERVER_URL = "https://scrawl.weber.edu.deal/api"  # 您的 Vercel 部署 URL


class CloudVariableClient:
    def __init__(self, server_url=SERVER_URL, project_id=None, api_key=None):
        self.server_url = server_url
        self.project_id = project_id
        self.api_key = api_key
        self.variables = {}
        
        # 如果没有提供项目ID，自动注册新项目
        if not project_id or not api_key:
            self.register_project()
    
    def register_project(self, project_name="TestProject"):
        """注册新项目"""
        url = f"{self.server_url}/register"
        payload = {"project_name": project_name}
        
        try:
            print(f"📤 注册项目: {project_name}")
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 201:
                data = response.json()
                self.project_id = data['project_id']
                self.api_key = data['api_key']
                print(f"✅ 项目注册成功! ID: {self.project_id}, API Key: {self.api_key}")
                return True
            else:
                print(f"❌ 项目注册失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                print(f"请求URL: {url}")
                print(f"请求负载: {payload}")
                return False
        except Exception as e:
            print(f"❌ 注册请求异常: {str(e)}")
            traceback.print_exc()
            return False
    
    def set_variable(self, var_name, var_value):
        """设置变量值"""
        if not self.project_id or not self.api_key:
            print("❌ 未设置项目ID或API密钥")
            return False
        
        url = f"{self.server_url}/{self.project_id}/set"
        headers = {"X-API-Key": self.api_key}
        payload = {"var_name": var_name, "var_value": var_value}
        
        try:
            print(f"📤 设置变量: {var_name} = {var_value}")
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ 设置变量成功: {var_name} = {var_value}")
                self.variables[var_name] = var_value
                return True
            else:
                print(f"❌ 设置变量失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                print(f"请求URL: {url}")
                print(f"请求头: {headers}")
                print(f"请求负载: {payload}")
                return False
        except Exception as e:
            print(f"❌ 设置变量异常: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_variable(self, var_name):
        """获取变量值"""
        if not self.project_id or not self.api_key:
            print("❌ 未设置项目ID或API密钥")
            return None
        
        url = f"{self.server_url}/{self.project_id}/get"
        headers = {"X-API-Key": self.api_key}
        params = {"var_name": var_name}
        
        try:
            print(f"📥 获取变量: {var_name}")
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                value = data['var_value']
                print(f"✅ 获取变量成功: {var_name} = {value}")
                self.variables[var_name] = value
                return value
            else:
                print(f"❌ 获取变量失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                print(f"请求URL: {url}")
                print(f"请求头: {headers}")
                print(f"请求参数: {params}")
                return None
        except Exception as e:
            print(f"❌ 获取变量异常: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_all_variables(self):
        """获取所有变量"""
        if not self.project_id or not self.api_key:
            print("❌ 未设置项目ID或API密钥")
            return {}
        
        url = f"{self.server_url}/{self.project_id}/all"
        headers = {"X-API-Key": self.api_key}
        
        try:
            print("📥 获取所有变量")
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                variables = response.json()
                print(f"✅ 获取所有变量成功: 共 {len(variables)} 个变量")
                self.variables = {k: v['value'] for k, v in variables.items()}
                return variables
            else:
                print(f"❌ 获取所有变量失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return {}
        except Exception as e:
            print(f"❌ 获取所有变量异常: {str(e)}")
            traceback.print_exc()
            return {}
    
    def health_check(self):
        """健康检查"""
        url = f"{self.server_url}/health"
        
        try:
            print("🩺 健康检查")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查通过: {data}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {str(e)}")
            traceback.print_exc()
            return False

# 获取当前包目录的绝对路径
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_resource_path(resource):
    # 组合包内其他文件的路径
    data_path = os.path.join(PACKAGE_DIR, resource)
    return data_path


def on_key(key: int, mode: str = "pressed"):
    """将函数标记为按键事件处理函数
    mode: 
        "pressed" - 按键按下瞬间触发（默认）
        "held" - 按键按住状态持续触发
        "released" - 按键释放时触发
    """

    def decorator(func):
        func._key_event = (key, mode)
        return func

    return decorator


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


def handle_edge_collision(edge: str = "any"):
    """将函数标记为碰到舞台边缘事件处理函数"""

    def decorator(func):
        func._edge_collision = edge
        return func

    return decorator


def handle_sprite_collision(target: [type, str]):
    """将函数标记为碰到指定类型或名称的精灵类事件处理函数"""

    def decorator(func):
        if not hasattr(func, '_sprite_collisions'):
            func._sprite_collisions = [] # 修改目的：支持标记检查多个碰撞
        func._sprite_collisions.append(target)
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
                fallback_fonts = [
                    "simhei.ttf", "simsun.ttc", "DroidSansFallbackFull.ttf",
                    "msyh.ttc", "WenQuanYiMicroHei.ttf"
                ]
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

        self.debug_info = []
        self.fps = 60
        self.background_color = (0, 0, 0)
        self.key_bindings = {}  # 全局按键绑定

        self.key_events = []  # 存储全局按键处理函数
        self.key_down_events = {}  # 存储按键按下的时间 {key: timestamp}
        self.debug = False

        self.broadcast_history = {}  # 存储广播触发状态
        self.current_frame_broadcasts = set()  # 当前帧触发的广播

        # 初始化音频系统
        pygame.mixer.init()
        self.sound_effects = {}  # 存储加载的音效
        self.music = {}  # 存储加载的背景音乐文件路径
        self.current_music = None  # 当前播放的音乐
        self.music_volume = 0.5  # 背景音乐音量 (0.0-1.0)
        self.sound_volume = 0.7  # 音效音量 (0.0-1.0)
        self.music_looping = False  # 背景音乐是否循环
        
    
    def run(self, fps: int = 60, debug: bool = False):
        self.debug = debug

        if not self.scene:
            print("No scene set!")
            return

        self.fps = fps
        self.running = True

        self.scene.game = self
        # self.scene.setup()

        while self.running:
            # 在每帧开始时清除广播状态
            self.current_frame_broadcasts.clear()

            self.current_time = pygame.time.get_ticks()

            # 保存上一帧的按键状态
            prev_key_down_events = dict(self.key_down_events)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                # 处理按键按下事件
                if event.type == pygame.KEYDOWN:
                    # 记录按键按下的时间
                    self.key_down_events[event.key] = self.current_time

                    # 先检查全局按键绑定
                    if event.key in self.key_bindings:
                        self.key_bindings[event.key]()
                    # 再检查场景按键绑定
                    elif self.scene and event.key in self.scene.key_bindings:
                        self.scene.key_bindings[event.key]()

                    # 处理按键按下事件
                    self.process_key_event(event.key, "pressed")

                # 处理按键释放事件
                if event.type == pygame.KEYUP:
                    # 处理按键释放事件
                    self.process_key_event(event.key, "released")
                    # 从按键状态中移除
                    if event.key in self.key_down_events:
                        del self.key_down_events[event.key]

                # 将事件传递给场景和精灵
                if self.scene:
                    self.scene.handle_event(event)
                    for sprite in self.scene.sprites:
                        sprite.handle_event(event)

            # 处理按住状态的事件
            self.process_held_keys(prev_key_down_events)

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
        
        self.close_cloud_variables()

        pygame.quit()
        sys.exit()
        
    def process_key_event(self, key: int, mode: str):
        """处理单个按键事件"""
        for obj, method, event_key, event_mode in self.key_events:
            if key == event_key and mode == event_mode:
                try:
                    self.add_task(method)
                except Exception as e:
                    self.log_debug(f"按键事件错误: {e}")

    def process_held_keys(self, prev_key_down_events: dict):
        """处理按住状态的事件"""
        for key, press_time in list(self.key_down_events.items()):
            # 检查按键是否被按住超过一帧
            if self.current_time - press_time > 1000 / self.fps:
                # 确保按键在上一帧也存在（不是刚按下的）
                if key in prev_key_down_events:
                    self.process_key_event(key, "held")

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

    def add_task(self, function, delay=0):
        self.tasks.append({
            'generator': function(),
            'next_run': self.current_time + delay
        })

    def setup_key_listeners(self, obj):
        """设置对象（场景或精灵）的按键监听器"""
        for name in dir(obj):
            method = getattr(obj, name)
            if callable(method) and hasattr(method, '_key_event'):
                key, mode = getattr(method, '_key_event')
                self.key_events.append((obj, method, key, mode))
                self.log_debug(
                    f"注册按键事件: {key} -> {obj.__class__.__name__}.{method.__name__} ({mode})"
                )

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
        if self.debug:
            self.debug_info.append(info)
    
    def mark_broadcast(self, event_name: str):
        """标记广播已被触发"""
        self.current_frame_broadcasts.add(event_name)
        self.broadcast_history[event_name] = self.current_time
    
    def received_broadcast(self, event_name: str) -> bool:
        """检查是否收到指定广播"""
        return event_name in self.current_frame_broadcasts

    def draw_debug_info(self):
        if not self.debug:  # 调试模式关闭时直接返回，不绘制
            return

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

    def load_sound(self, name: str, file_path: str):
        """加载音效文件并存储在游戏中"""
        try:
            sound = pygame.mixer.Sound(get_resource_path(file_path))
            self.sound_effects[name] = sound
            self.log_debug(f"Loaded sound: {name}")
        except Exception as e:
            self.log_debug(f"Failed to load sound {name}: {e}")
    
    def load_music(self, name: str, file_path: str):
        """加载背景音乐文件路径（实际播放时才加载）"""
        self.music[name] = get_resource_path(file_path)
        self.log_debug(f"Registered music: {name}")
    
    def play_sound(self, name: str, volume: float = None):
        """播放音效"""
        if name not in self.sound_effects:
            self.log_debug(f"Sound not found: {name}")
            return
            
        sound = self.sound_effects[name]
        if volume is not None:
            sound.set_volume(max(0.0, min(1.0, volume)))  # 确保音量在0-1之间
        else:
            sound.set_volume(self.sound_volume)
            
        sound.play()
    
    def play_music(self, name: str, loops: int = -1, volume: float = None):
        """播放背景音乐（loops=-1表示无限循环）"""
        if name not in self.music:
            self.log_debug(f"Music not found: {name}")
            return
            
        pygame.mixer.music.load(self.music[name])
        
        if volume is not None:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        else:
            pygame.mixer.music.set_volume(self.music_volume)
            
        pygame.mixer.music.play(loops)
        self.current_music = name
        self.music_looping = (loops == -1)
    
    def stop_music(self):
        """停止背景音乐"""
        pygame.mixer.music.stop()
        self.current_music = None
    
    def pause_music(self):
        """暂停背景音乐"""
        pygame.mixer.music.pause()
    
    def unpause_music(self):
        """继续播放背景音乐"""
        pygame.mixer.music.unpause()
    
    def set_music_volume(self, volume: float):
        """设置背景音乐音量 (0.0-1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sound_volume(self, volume: float):
        """设置音效音量 (0.0-1.0)"""
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sound_effects.values():
            sound.set_volume(self.sound_volume)
    
    def play_drum(self, drum_type: str, duration: int = 100):
        """播放鼓声（类似Scratch的鼓声效果）"""
        # 使用内置的鼓声效果
        frequencies = {
            "bass": 60,   # 低音鼓
            "snare": 200,  # 小鼓
            "hihat": 1000, # 踩镲
            "cymbal": 1500 # 铙钹
        }
        
        if drum_type not in frequencies:
            self.log_debug(f"Unknown drum type: {drum_type}")
            return
            
        # 生成简单的鼓声波形
        sample_rate = 44100
        samples = int(sample_rate * duration / 1000)
        buf = numpy.zeros((samples, 2), dtype=numpy.int16)
        
        max_amplitude = 32767
        decay = 0.997  # 衰减系数
        
        # 创建衰减的正弦波
        for s in range(samples):
            t = float(s) / sample_rate
            amplitude = max_amplitude * math.exp(-t * 10)  # 指数衰减
            wave = amplitude * math.sin(2 * math.pi * frequencies[drum_type] * t)
            buf[s][0] = int(wave)
            buf[s][1] = int(wave)
            
        # 创建并播放声音
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.sound_volume)
        sound.play()
    
    def play_note(self, note: str, duration: int = 500):
        """播放音符（类似Scratch的音符效果）"""
        # 音符到频率的映射
        note_freq = {
            "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
            "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25
        }
        
        if note not in note_freq:
            self.log_debug(f"Unknown note: {note}")
            return
            
        # 生成简单的正弦波
        sample_rate = 44100
        samples = int(sample_rate * duration / 1000)
        buf = numpy.zeros((samples, 2), dtype=numpy.int16)
        
        max_amplitude = 32767
        freq = note_freq[note]
        
        for s in range(samples):
            t = float(s) / sample_rate
            wave = max_amplitude * math.sin(2 * math.pi * freq * t)
            buf[s][0] = int(wave)
            buf[s][1] = int(wave)
            
        # 创建并播放声音
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.sound_volume)
        sound.play()


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
                self.game.add_task(task)

        # 原有的main函数处理
        if hasattr(self, 'main') and callable(self.main):
            self.game.add_task(self.main)

        for sprite in self.sprites:
            sprite.setup(self)

        # 收集按键事件监听器
        if self.game:
            self.game.setup_key_listeners(self)

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
        
        # 标记广播已被触发
        self.game.mark_broadcast(event_name)

        self.game.log_debug(f"Broadcasting event: {event_name}")

        # 优先调用匹配的装饰器处理函数
        for sprite in self.sprites:
            if event_name in sprite.broadcast_handlers:
                for handler in sprite.broadcast_handlers[event_name]:
                    self.game.add_task(handler)

        # 其次调用名为"on_{event_name}"的函数
        on_event_name = f"on_{event_name}"
        for sprite in self.sprites:
            if hasattr(sprite, on_event_name) and callable(
                    getattr(sprite, on_event_name)):
                self.game.add_task(getattr(sprite, on_event_name))

        # 场景自身的事件处理
        if hasattr(self, on_event_name) and callable(
                getattr(self, on_event_name)):
            self.game.add_task(getattr(self, on_event_name))

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

    def received_broadcast(self, event_name: str) -> bool:
        """精灵检查是否收到广播的辅助方法"""
        if self.game:
            return self.game.received_broadcast(event_name)
        return False

    def play_sound(self, name: str, volume: float = None):
        """场景播放音效"""
        if self.game:
            self.game.play_sound(name, volume)
    
    def play_music(self, name: str, loops: int = -1, volume: float = None):
        """场景播放背景音乐"""
        if self.game:
            self.game.play_music(name, loops, volume)
    
    def play_drum(self, drum_type: str, duration: int = 100):
        """场景播放鼓声"""
        if self.game:
            self.game.play_drum(drum_type, duration)
    
    def play_note(self, note: str, duration: int = 500):
        """场景播放音符"""
        if self.game:
            self.game.play_note(note, duration)
    
    def stop_music(self):
        """场景停止背景音乐"""
        if self.game:
            self.game.stop_music()
    
    def set_music_volume(self, volume: float):
        """场景设置背景音乐音量"""
        if self.game:
            self.game.set_music_volume(volume)
    
    def set_sound_volume(self, volume: float):
        """场景设置音效音量"""
        if self.game:
            self.game.set_sound_volume(volume)


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

        self.collision_mask = None  # 存储用于碰撞检测的mask
        self.edge_handlers = {}  # 存储碰到舞台边缘的事件处理函数
        self.sprite_collision_handlers = []  # 存储碰到其他精灵的事件处理函数
        self._last_edge = None  # 记录上次碰撞的边缘
        self._collided_sprites = set()  # 记录当前碰撞的精灵ID

        # 添加碰撞检测标志
        self.needs_edge_collision = False
        self.needs_sprite_collision = False
        self.collision_targets = set()  # 存储需要检测的精灵名称
        
        # 添加移动状态变量
        self._is_moving = False  # 是否正在移动
        self._active_movement = None  # 当前活动移动的方向标识

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

    def _create_mask(self):
        """如果当前图像有alpha通道，创建碰撞mask"""
        image = self.image
        if image is not None and image.get_flags() & pygame.SRCALPHA:
            # 创建带缩放和旋转的mask
            if self.size != 1.0:
                orig_size = image.get_size()
                new_size = (int(orig_size[0] * self.size),
                            int(orig_size[1] * self.size))
                scaled_img = pygame.transform.scale(image, new_size)
            else:
                scaled_img = image

            if self.direction != 0:
                rotated_img = pygame.transform.rotate(scaled_img,
                                                      self.direction - 90)
                self.collision_mask = pygame.mask.from_surface(rotated_img)
            else:
                self.collision_mask = pygame.mask.from_surface(scaled_img)
        else:
            self.collision_mask = None

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
                    self.game.add_task(task)

            # 原有的main函数处理
            if hasattr(self, 'main') and callable(self.main):
                self.game.add_task(self.main)
        else:
            # 添加所有克隆任务到游戏队列
            for task in self.clones_tasks:
                if hasattr(task, '__call__'):
                    self.game.add_task(task)

            # 原有的克隆函数处理
            if hasattr(self, 'clones') and callable(self.clones):
                self.game.add_task(self.clones)

        # 收集所有标记为@handle_edge_collision的函数
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and hasattr(method, '_edge_collision'):
                edge = getattr(method, '_edge_collision')
                self.edge_handlers[edge] = method

        # 收集所有标记为@handle_sprite_collision的函数
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and hasattr(method, '_sprite_collisions'):
                # 处理多个碰撞目标
                for target in method._sprite_collisions:
                    self.sprite_collision_handlers.append((method, target))

        # 收集按键事件监听器
        if self.scene and self.scene.game:
            self.scene.game.setup_key_listeners(self)


        # 检查是否有边缘碰撞处理函数
        self.needs_edge_collision = bool(self.edge_handlers)

        # 检查是否有精灵碰撞处理函数
        self.needs_sprite_collision = bool(self.sprite_collision_handlers) # 避免大量无用的检测，优化性能 待测试: Scratch的碰到...?功能 collide_with()

        # 收集需要检测的精灵名称
        for handler in self.sprite_collision_handlers:
            target = getattr(handler, '_sprite_collision', None)
            if isinstance(target, str):
                self.collision_targets.add(target)

        # 更新碰撞检测标志
        self._update_collision_flags()

    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self):
        """基础精灵更新逻辑"""
        if not self.game:
            return

        # 更新说话气泡（这部分无论是否需要碰撞检测都要执行）
        if self.speech and self.speech_timer > 0:
            self.speech_timer -= self.game.clock.get_time()
            if self.speech_timer <= 0:
                self.speech = None

        # 只执行必要的碰撞检测
        self._perform_collision_detection()

    def _perform_collision_detection(self):
        """执行必要的碰撞检测"""
        # 检测舞台边缘碰撞（如果精灵需要）
        if self.needs_edge_collision and self.collision_radius:
            current_edge = None

            # 计算精灵边界
            x, y = self.pos.x, self.pos.y
            radius = self.collision_radius * self.size

            if x - radius <= 0:
                current_edge = "left"
            elif x + radius >= self.game.width:
                current_edge = "right"
            elif y - radius <= 0:
                current_edge = "top"
            elif y + radius >= self.game.height:
                current_edge = "bottom"

            # 只在边缘发生变化时触发碰撞事件
            if current_edge and current_edge != self._last_edge:
                self._on_edge_collision(current_edge)
                self._last_edge = current_edge
            elif not current_edge:
                self._last_edge = None

        # 检测精灵碰撞（如果精灵需要）
        if self.needs_sprite_collision and self.scene and self.scene.sprites:
            current_frame_collisions = set()

            # 遍历场景中的所有精灵
            for other in self.scene.sprites:
                # 跳过自己和不可见的精灵
                if other is self or not other.visible:
                    continue

                # 如果设置了目标名称，只检测匹配的精灵
                if self.collision_targets and other.name not in self.collision_targets:
                    continue

                # 检查碰撞
                if self.collides_with(other):
                    # 记录当前碰撞
                    current_frame_collisions.add(id(other))

                    # 如果是新的碰撞（上一帧未发生），触发碰撞事件
                    if id(other) not in self._collided_sprites:
                        self._on_sprite_collision(other)

            # 更新碰撞记录
            self._collided_sprites = current_frame_collisions


    def broadcast(self, event_name: str):
        """广播事件，使所有精灵和场景都能响应"""
        #! 说不定要添加Game的广播方法
        if self.scene:
            self.scene.broadcast(event_name)

    def received_broadcast(self, event_name: str) -> bool:
        """场景检查是否收到广播的辅助方法"""
        if self.game:
            return self.game.received_broadcast(event_name)
        return False

    def collides_with(self, other: "Sprite") -> bool:
        """检查两个精灵是否碰撞"""
        if not self.visible or not other.visible:
            return False

        # 优先使用mask碰撞检测（如果两者都有mask）
        if self.collision_mask and other.collision_mask:
            # 计算两个精灵的位置差
            offset_x = int(other.pos.x - self.pos.x)
            offset_y = int(other.pos.y - self.pos.y)

            # 检查mask是否有重叠
            return self.collision_mask.overlap(
                other.collision_mask, (offset_x, offset_y)) is not None

        # 如果没有mask，使用圆形碰撞检测作为后备
        # 计算两个精灵之间的距离
        dx = self.pos.x - other.pos.x
        dy = self.pos.y - other.pos.y
        distance = math.sqrt(dx * dx + dy * dy)  # 使用欧几里得距离公式

        # 获取半径
        my_radius = self.collision_radius * self.size
        other_radius = other.collision_radius * other.size

        # 检查是否碰撞
        return distance < (my_radius + other_radius)

    def _on_edge_collision(self, edge: str):
        """触发碰到舞台边缘事件"""
        # 在游戏日志中记录
        if self.game:
            self.game.log_debug(
                f"Edge collision: {self.name} hit {edge} border")

        # 调用标记为@handle_edge_collision的函数
        for edge_name, handler in self.edge_handlers.items():
            if edge_name == edge or edge_name == "any":
                # 如果需要传递参数
                if "edge" in handler.__code__.co_varnames:
                    # 直接调用处理函数并传递参数
                    try:
                        result = handler(edge)
                        if hasattr(result, '__next__'):  # 如果返回生成器
                            self.scene.game.add_task(result)
                    except TypeError:
                        # 如果函数不接受参数，尝试无参数调用
                        result = handler()
                        if hasattr(result, '__next__'):
                            self.scene.game.add_task(result)
                else:
                    # 直接调用处理函数
                    try:
                        result = handler()
                        if hasattr(result, '__next__'):  # 如果返回生成器
                            self.scene.game.add_task(result)
                    except TypeError:
                        pass

    def _on_sprite_collision(self, other: "Sprite"):
        """触发碰到其他精灵事件"""
        for handler, expected_target in self.sprite_collision_handlers:
            # 检测逻辑分为三种情况：
            if expected_target is None:  # 无参数装饰器，匹配所有精灵
                valid = True
            elif isinstance(expected_target, type):  # 按类型匹配
                valid = isinstance(other, expected_target)
            elif isinstance(expected_target, str):  # 按名称匹配
                valid = other.name == expected_target
            else:
                continue
                
            if valid:
                if "other" in handler.__code__.co_varnames:
                    try:
                        result = handler(other)
                        if hasattr(result, '__next__'):
                            self.scene.game.add_task(result)
                    except TypeError:
                        result = handler()
                        if hasattr(result, '__next__'):
                            self.scene.game.add_task(result)
                else:
                    try:
                        result = handler()
                        if hasattr(result, '__next__'):
                            self.scene.game.add_task(result)
                    except TypeError:
                        pass

    def _update_collision_flags(self):
        """更新碰撞检测标志"""
        # 检查是否有边缘碰撞处理函数
        self.needs_edge_collision = bool(self.edge_handlers)

        # 检查是否有精灵碰撞处理函数
        self.needs_sprite_collision = bool(self.sprite_collision_handlers)

        # 收集需要检测的精灵名称
        for handler in self.sprite_collision_handlers:
            target = getattr(handler, '_sprite_collision', None)
            if isinstance(target, str):
                self.collision_targets.add(target)
    
    def touches_color(self, color: Tuple[int, int, int], tolerance: int = 0) -> bool:
        """检查精灵边缘是否触碰到指定颜色
        
        Args:
            color: 目标颜色 (R, G, B)
            tolerance: 颜色容差范围 (0-255)，默认0表示完全匹配
            
        Returns:
            bool: 精灵边缘是否触碰到目标颜色
        """
        if not self.game or not self.visible:
            return False
            
        # 获取精灵边缘点（圆形或基于图像的轮廓）
        edge_points = self._get_edge_points()
        
        # 检查每个边缘点是否碰到目标颜色
        for point in edge_points:
            if self._point_touches_color(point, color, tolerance):
                return True
                
        return False
        
    def _get_edge_points(self) -> List[Tuple[int, int]]:
        """获取精灵边缘的点（用于颜色碰撞检测）"""
        points = []
        center_x, center_y = int(self.pos.x), int(self.pos.y)
        radius = int(self.collision_radius * self.size)
        
        # 如果精灵有图像，使用基于图像的轮廓点
        if self.image:
            # 获取缩放和旋转后的图像
            if self.size != 1.0:
                orig_size = self.image.get_size()
                new_size = (int(orig_size[0] * self.size),
                            int(orig_size[1] * self.size))
                scaled_img = pygame.transform.scale(self.image, new_size)
            else:
                scaled_img = self.image
                
            if self.direction != 0:
                rotated_img = pygame.transform.rotate(scaled_img, self.direction - 90)
            else:
                rotated_img = scaled_img
                
            # 获取轮廓点（每隔5度取一个点）
            mask = pygame.mask.from_surface(rotated_img)
            if mask:
                rect = rotated_img.get_rect(center=(center_x, center_y))
                outline = mask.outline()
                
                # 简化轮廓点（每隔5个点取一个）
                for i in range(0, len(outline), 5):
                    x, y = outline[i]
                    points.append((x + rect.x, y + rect.y))
            else:
                # 如果没有mask，使用圆形轮廓作为后备
                for angle in range(0, 360, 10):
                    rad = math.radians(angle)
                    x = center_x + radius * math.cos(rad)
                    y = center_y + radius * math.sin(rad)
                    points.append((int(x), int(y)))
        else:
            # 没有图像时使用圆形轮廓
            for angle in range(0, 360, 10):
                rad = math.radians(angle)
                x = center_x + radius * math.cos(rad)
                y = center_y + radius * math.sin(rad)
                points.append((int(x), int(y)))
                
        return points
        
    def _point_touches_color(self, point: Tuple[int, int], 
                             target_color: Tuple[int, int, int], 
                             tolerance: int) -> bool:
        """检查特定点是否触碰到目标颜色"""
        # 确保点在屏幕范围内
        x, y = point
        if x < 0 or x >= self.game.width or y < 0 or y >= self.game.height:
            return False
            
        # 获取该点的颜色
        try:
            # 直接从屏幕表面获取颜色
            screen_color = self.game.screen.get_at((x, y))[:3]
        except IndexError:
            return False
            
        # 检查颜色是否匹配（考虑容差）
        return self._colors_match(screen_color, target_color, tolerance)
        
    def _colors_match(self, color1: Tuple[int, int, int], 
                      color2: Tuple[int, int, int], 
                      tolerance: int) -> bool:
        """检查两个颜色是否在容差范围内匹配"""
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        return (abs(r1 - r2) <= tolerance and \
               abs(g1 - g2) <= tolerance and \
               abs(b1 - b2) <= tolerance)

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

        # 确保不出边界 已废弃
        '''
        radius = self.collision_radius
        if radius > 0:
            self.pos.x = max(radius, min(self.game.width - radius, self.pos.x))
            self.pos.y = max(radius, min(self.game.height - radius,
                                         self.pos.y))
        '''
        if self.pen_down:
            self.pen_path.append((int(self.pos.x), int(self.pos.y)))
    
    def move_left(self, distance: float, prevent_boundary: bool = True):
        """向左移动指定距离
        
        Args:
            distance: 移动距离（像素）
            prevent_boundary: 是否阻止移出边界（默认为True）
        """
        new_x = self.pos.x - distance
        
        if prevent_boundary and self.game:
            radius = self.collision_radius * self.size
            new_x = max(radius, new_x)  # 确保不超出左边界
        
        self.pos.x = new_x
        
        # 记录画笔轨迹
        if self.pen_down:
            self.pen_path.append((int(self.pos.x), int(self.pos.y)))

    def move_right(self, distance: float, prevent_boundary: bool = True):
        """向右移动指定距离
        
        Args:
            distance: 移动距离（像素）
            prevent_boundary: 是否阻止移出边界（默认为True）
        """
        new_x = self.pos.x + distance
        
        if prevent_boundary and self.game:
            radius = self.collision_radius * self.size
            new_x = min(self.game.width - radius, new_x)  # 确保不超出右边界
        
        self.pos.x = new_x
        
        # 记录画笔轨迹
        if self.pen_down:
            self.pen_path.append((int(self.pos.x), int(self.pos.y)))

    def move_up(self, distance: float, prevent_boundary: bool = True):
        """向上移动指定距离
        
        Args:
            distance: 移动距离（像素）
            prevent_boundary: 是否阻止移出边界（默认为True）
        """
        new_y = self.pos.y - distance
        
        if prevent_boundary and self.game:
            radius = self.collision_radius * self.size
            new_y = max(radius, new_y)  # 确保不超出上边界
        
        self.pos.y = new_y
        
        # 记录画笔轨迹
        if self.pen_down:
            self.pen_path.append((int(self.pos.x), int(self.pos.y)))

    def move_down(self, distance: float, prevent_boundary: bool = True):
        """向下移动指定距离
        
        Args:
            distance: 移动距离（像素）
            prevent_boundary: 是否阻止移出边界（默认为True）
        """
        new_y = self.pos.y + distance
        
        if prevent_boundary and self.game:
            radius = self.collision_radius * self.size
            new_y = min(self.game.height - radius, new_y)  # 确保不超出下边界
        
        self.pos.y = new_y
        
        # 记录画笔轨迹
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
        dy = self.pos.y - y  # 转换屏幕dy到数学坐标系
        angle_rad = math.atan2(dy, dx)  # 使用正确的dx和dy计算角度
        self.direction = math.degrees(angle_rad) % 360

    
    def glide_to(self, target_x: float, target_y: float, duration: float = 1000,easing: str = "linear"):
        """在指定时间内平滑移动到目标位置
        
        Args:
            target_x: 目标位置的x坐标
            target_y: 目标位置的y坐标
            duration: 移动所需时间（毫秒）
            easing: 缓动函数类型 ("linear", "ease_in", "ease_out", "ease_in_out")
        """
        if not self.game:
            return
        
        start_x, start_y = self.pos.x, self.pos.y
        start_time = self.game.current_time
        end_time = start_time + duration
        
        while self.game.current_time < end_time:
            # 计算当前进度（0.0 - 1.0）
            progress = (self.game.current_time - start_time) / duration
            progress = min(progress, 1.0)  # 确保不超过1.0
            
            # 应用缓动函数
            if easing == "ease_in_out":
                # 三次贝塞尔曲线缓动
                progress = progress * progress * (3 - 2 * progress)
            elif easing == "ease_in":
                # 加速缓动
                progress = progress * progress
            elif easing == "ease_out":
                # 减速缓动
                progress = 1 - (1 - progress) * (1 - progress)
            # 默认为线性
            
            # 计算新位置
            self.pos.x = start_x + (target_x - start_x) * progress
            self.pos.y = start_y + (target_y - start_y) * progress
            
            # 等待下一帧
            yield 0
        
        # 确保最终位置准确
        self.pos.x = target_x
        self.pos.y = target_y
    
    
    def glide_in_direction(self, direction: float, distance: float, 
                           duration: float = 1000, easing: str = "linear",
                           exclusive: bool = True):
        """
        向指定方向平滑移动指定距离
        
        Args:
            direction: 移动方向（角度，0表示右，90表示上）
            distance: 移动距离（像素）
            duration: 移动所需时间（毫秒）
            easing: 缓动函数类型 ("linear", "ease_in", "ease_out", "ease_in_out")
            exclusive: 是否启用方向互斥（默认为True）
        """
        # 计算目标位置
        rad = math.radians(direction)
        dx = distance * math.cos(rad)
        dy = -distance * math.sin(rad)  # 注意：屏幕坐标系y轴向下
        
        # 检查是否应该互斥移动
        if exclusive and self._is_moving:
            # 检查新移动是否与当前活动移动冲突
            if self._is_conflicting_movement(direction):
                # 取消新移动
                return
        
        # 设置移动状态
        self._is_moving = True
        self._active_movement = self._get_movement_type(direction)
        
        # 计算目标位置
        target_x = self.pos.x + dx
        target_y = self.pos.y + dy
        
        # 执行移动
        if not self.game:
            return
        
        start_x, start_y = self.pos.x, self.pos.y
        start_time = self.game.current_time
        end_time = start_time + duration
        
        while self.game.current_time < end_time:
            # 检查是否应该互斥移动
            if exclusive and self._is_moving:
                # 检查新移动是否与当前活动移动冲突
                if self._is_conflicting_movement(direction):
                    # 取消新移动
                    return

            # 计算当前进度（0.0 - 1.0）
            progress = (self.game.current_time - start_time) / duration
            progress = min(progress, 1.0)  # 确保不超过1.0
            
            # 应用缓动函数
            if easing == "ease_in_out":
                # 三次贝塞尔曲线缓动
                progress = progress * progress * (3 - 2 * progress)
            elif easing == "ease_in":
                # 加速缓动
                progress = progress * progress
            elif easing == "ease_out":
                # 减速缓动
                progress = 1 - (1 - progress) * (1 - progress)
            # 默认为线性
            
            # 计算新位置
            self.pos.x = start_x + (target_x - start_x) * progress
            self.pos.y = start_y + (target_y - start_y) * progress
            
            # 等待下一帧
            yield 0
        
        # 确保最终位置准确
        self.pos.x = target_x
        self.pos.y = target_y
        
        # 移动完成后重置状态
        self._is_moving = False
        self._active_movement = None
    
    def _get_movement_type(self, direction: float) -> str:
        """获取移动方向类型"""
        # 将角度标准化到0-360度
        normalized_direction = direction % 360
        
        # 判断主要方向
        if 315 <= normalized_direction or normalized_direction < 45:
            return "right"
        elif 45 <= normalized_direction < 135:
            return "up"
        elif 135 <= normalized_direction < 225:
            return "left"
        else:  # 225 <= normalized_direction < 315
            return "down"
    
    def _is_conflicting_movement(self, new_direction: float) -> bool:
        """检查新移动是否与当前活动移动冲突"""
        if not self._active_movement:
            return False
        
        new_type = self._get_movement_type(new_direction)
        current_type = self._active_movement
        
        # 检查是否在同一个冲突组
        if current_type == "left" and new_type == "right":
            return True
        elif current_type == "right" and new_type == "left":
            return True
        elif current_type == "up" and new_type == "down":
            return True
        elif current_type == "down" and new_type == "up":
            return True
        
        return False

    # 更新方向移动方法以使用新的互斥功能
    def glide_left(self, distance: float, duration: float = 1000, 
                   easing: str = "linear", exclusive: bool = True):
        """向左平滑移动指定距离（支持互斥）"""
        yield from self.glide_in_direction(180, distance, duration, easing, exclusive)

    def glide_right(self, distance: float, duration: float = 1000, 
                    easing: str = "linear", exclusive: bool = True):
        """向右平滑移动指定距离（支持互斥）"""
        yield from self.glide_in_direction(0, distance, duration, easing, exclusive)

    def glide_up(self, distance: float, duration: float = 1000, 
                 easing: str = "linear", exclusive: bool = True):
        """向上平滑移动指定距离（支持互斥）"""
        yield from self.glide_in_direction(90, distance, duration, easing, exclusive)

    def glide_down(self, distance: float, duration: float = 1000, 
                   easing: str = "linear", exclusive: bool = True):
        """向下平滑移动指定距离（支持互斥）"""
        yield from self.glide_in_direction(270, distance, duration, easing, exclusive)

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

    def clone(self, other_sprite: 'Sprite' = None):
        """克隆精灵（支持克隆自己或其他精灵）

        Args:
            other_sprite: 要克隆的目标精灵（默认None表示克隆自己）
        """
        if not self.scene or not self.game:
            return

        target = other_sprite if other_sprite else self

        # 限制克隆数量
        if len(self.scene.sprites) >= 500:
            return

        # 克隆操作（支持克隆任意精灵）
        clone = target.__class__()

        # 复制基本属性
        clone.pos = pygame.Vector2(target.pos)
        clone.direction = target.direction
        clone.size = target.size
        clone.color = target.color
        clone.costumes = target.costumes.copy()
        clone.current_costume = target.current_costume
        clone._default_image = target._default_image
        clone.collision_radius = target.collision_radius

        clone.is_clones = True

        # 添加到当前场景
        self.scene.add_sprite(clone)
        self.game.log_debug(f"Cloned sprite: {target.name}")

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

    def face_towards(self, target: Any):
        """让精灵面向特定目标。

        参数:
            target: 可以是以下类型之一:
                - pygame.Vector2: 面向特定坐标
                - tuple (x, y): 面向特定坐标
                - Sprite: 面向另一个精灵
                - "mouse": 面向鼠标位置
                - "edge": 面向最近的舞台边缘
                - str: 面向场景中name属性相符的精灵（用户保证唯一）
        """
        # 处理字符串参数（精灵名称）
        if isinstance(target, str):
            # 在当前场景中查找名称相符的精灵
            matching_sprites = [
                sprite for sprite in self.scene.sprites
                if sprite.name == target
            ]

            if not matching_sprites:
                # 如果没有找到匹配的精灵
                if self.game:
                    self.game.log_debug(
                        f"No sprite named '{target}' found to face towards")
                return

            # 用户保证只有一个匹配项，所以取第一个
            target_sprite = matching_sprites[0]
            self.point_towards(target_sprite.pos.x, target_sprite.pos.y)
            return

        # 处理坐标点
        if isinstance(target, pygame.Vector2):
            self.point_towards(target.x, target.y)
        elif isinstance(target, tuple) and len(target) == 2:
            x, y = target
            self.point_towards(x, y)

        # 处理其他精灵
        elif isinstance(target, Sprite):
            self.point_towards(target.pos.x, target.pos.y)

        # 处理特殊关键字
        elif target == "mouse":
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.point_towards(mouse_x, mouse_y)

        elif target == "edge":
            # 计算到各边缘的距离
            distances = {
                "left": self.pos.x,
                "right": self.game.width - self.pos.x,
                "top": self.pos.y,
                "bottom": self.game.height - self.pos.y,
            }

            # 找到最近的边缘
            closest_edge = min(distances, key=distances.get)

            # 指向最近边缘的中心位置
            if closest_edge == "left":
                self.point_towards(0, self.pos.y)
            elif closest_edge == "right":
                self.point_towards(self.game.width, self.pos.y)
            elif closest_edge == "top":
                self.point_towards(self.pos.x, 0)
            elif closest_edge == "bottom":
                self.point_towards(self.pos.x, self.game.height)

    def face_random_direction(self):
        """让精灵指向随机方向"""
        self.direction = random.randint(0, 359)

    def face_horizontal(self, degrees: float = 0):
        """水平面向特定方向
        参数:
            degrees: 
                0 - 右方
                180 - 左方
                90 - 上 (默认Scratch方向，y轴向下)
                270 - 下
        """
        self.point_in_direction(degrees)

    def face_vertical(self, degrees: float = 90):
        """垂直面向特定方向
        参数:
            degrees: 
                90 - 上 (默认方向)
                270 - 下
        """
        self.point_in_direction(degrees)

    def face_away_from(self, target: Any):
        """背向特定目标"""
        self.face_towards(target)
        self.point_in_direction((self.direction + 180) % 360)

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

    def play_sound(self, name: str, volume: float = None):
        """精灵播放音效"""
        if self.game:
            self.game.play_sound(name, volume)
    
    def play_music(self, name: str, loops: int = -1, volume: float = None):
        """精灵播放背景音乐"""
        if self.game:
            self.game.play_music(name, loops, volume)
    
    def play_drum(self, drum_type: str, duration: int = 100):
        """精灵播放鼓声"""
        if self.game:
            self.game.play_drum(drum_type, duration)
    
    def play_note(self, note: str, duration: int = 500):
        """精灵播放音符"""
        if self.game:
            self.game.play_note(note, duration)
    
    def stop_music(self):
        """精灵停止背景音乐"""
        if self.game:
            self.game.stop_music()
    
    def set_music_volume(self, volume: float):
        """精灵设置背景音乐音量"""
        if self.game:
            self.game.set_music_volume(volume)
    
    def set_sound_volume(self, volume: float):
        """精灵设置音效音量"""
        if self.game:
            self.game.set_sound_volume(volume)

class Cat(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "Cat"

        self.add_costume("costume1",
                         pygame.image.load(get_resource_path("cat1.svg")).convert_alpha())
        self.add_costume("costume2",
                         pygame.image.load(get_resource_path("cat2.svg")).convert_alpha())

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