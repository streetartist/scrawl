import pygame
import sys
import types
import math
import random
from collections import deque
from typing import Tuple, List, Callable, Any, Dict, Optional
import os
import numpy
import inspect  # 引入inspect模块

import threading
import time
import requests
import json
import uuid
from collections import deque

class CloudVariablesClient:
    def __init__(self, project_id=None, base_url="http/1.117.220.147:5000", sync_interval=100):
        self.base_url = base_url
        self.sync_interval = sync_interval/1000  # 毫秒化秒
        self.local_vars = {}              # 本地变量存储
        self.change_queue = deque()       # 变更队列 (线程安全)
        self.lock = threading.Lock()      # 线程锁
        self.running = True               # 控制同步线程运行
        
        # 注册新项目或使用现有项目
        if project_id:
            self.project_id = project_id
        else:
            self._register_project()
        
        # 从服务器加载所有变量
        self._load_all_variables()
        
        # 启动同步线程
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()

    def _register_project(self):
        """注册新项目并获取project_id"""
        url = f"{self.base_url}/api/register"
        try:
            response = requests.post(url)
            response.raise_for_status()
            data = response.json()
            self.project_id = data['project_id']
            print(f"项目注册成功! ID: {self.project_id}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"连接服务器失败: {str(e)}")

    def _load_all_variables(self):
        """从服务器加载所有变量到本地"""
        url = f"{self.base_url}/api/{self.project_id}/all"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            server_vars = response.json()
            
            with self.lock:
                self.local_vars = {}
                for var_name, var_data in server_vars.items():
                    # 直接存储解析后的值
                    self.local_vars[var_name] = var_data['value']
        except requests.exceptions.RequestException:
            print("警告: 无法从服务器加载初始变量")
        except json.JSONDecodeError:
            print("错误: 服务器返回了无效的JSON数据")

    def set_variable(self, var_name, value):
        """设置变量值（线程安全）"""
        with self.lock:
            # 检查值是否实际变化
            if var_name in self.local_vars and self.local_vars[var_name] == value:
                return
            
            # 更新本地值
            self.local_vars[var_name] = value
            
            # 添加到变更队列
            self.change_queue.append((var_name, value))

    def get_variable(self, var_name, default=None):
        """获取变量值（线程安全）"""
        with self.lock:
            return self.local_vars.get(var_name, default)

    def get_all_variables(self):
        """获取所有变量副本（线程安全）"""
        with self.lock:
            return self.local_vars.copy()

    def _sync_changes(self):
        """同步变更到服务器"""
        if not self.change_queue:
            return
        
        # 批量准备变更
        changes = []
        while self.change_queue:
            changes.append(self.change_queue.popleft())
        
        # 准备批量更新数据
        update_data = [{
            'var_name': var_name,
            'var_value': value
        } for var_name, value in changes]
        
        # 发送批量更新请求
        headers = {'Content-Type': 'application/json'}
        url = f"{self.base_url}/api/{self.project_id}/batch_update"
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                json={'updates': update_data}
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"同步失败: {str(e)}")
            # 重新加入队列以便重试
            with self.lock:
                for change in changes:
                    self.change_queue.appendleft(change)

    def _fetch_updates(self):
        """从服务器获取更新"""
        url = f"{self.base_url}/api/{self.project_id}/all"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            server_vars = response.json()
            
            with self.lock:
                # 只更新本地未修改的变量
                for var_name, var_data in server_vars.items():
                    # 检查此变量是否有未同步的本地修改
                    has_pending_change = any(
                        name == var_name for name, _ in self.change_queue
                    )
                    
                    if not has_pending_change:
                        self.local_vars[var_name] = var_data['value']
        except requests.exceptions.RequestException:
            pass  # 网络错误时静默失败

    def _sync_loop(self):
        """同步循环：定期执行同步"""
        while self.running:
            try:
                # 第一步：推送本地变更
                self._sync_changes()
                
                # 第二步：获取服务器更新
                self._fetch_updates()
            except Exception as e:
                print(f"同步错误: {str(e)}")
            
            time.sleep(self.sync_interval)

    def close(self):
        """关闭客户端并停止同步"""
        self.running = False
        self.sync_thread.join(timeout=2.0)
        
        # 最后尝试同步所有变更
        self._sync_changes()
        print("云变量客户端已关闭")

# 获取当前包目录的绝对路径
# NOTE: This will fail if not run as a package. For a single script, use '.'
try:
    PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PACKAGE_DIR = os.path.abspath('.')


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

# 添加鼠标事件装饰器
def on_mouse_event(mode: str = "pressed", button: int = 1):
    """将函数标记为鼠标事件处理函数
    mode: 
        "pressed" - 鼠标按下瞬间触发
        "held" - 鼠标按住状态持续触发
        "released" - 鼠标释放时触发
    button:
        1 - 左键
        2 - 中键
        3 - 右键
    """
    def decorator(func):
        func._mouse_event = (button, mode)
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
            self.screen = pygame.display.set_mode((width, height), pygame.SCALED | pygame.FULLSCREEN)
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
        
        self.mouse_pos = (0, 0)  # 当前鼠标位置
        self.mouse_pressed = False  # 鼠标是否按下
        self.mouse_clicked = False  # 鼠标是否刚刚点击
        self.mouse_released = False  # 鼠标是否刚刚释放
        self.mouse_held_time = 0  # 鼠标持续按下的时间
        self.mouse_events = []  # 存储鼠标事件处理函数
        
    
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
            
            self.mouse_clicked = False  # 每帧开始时重置点击状态
            self.mouse_released = False  # 每帧开始时重置释放状态

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
                
                # 处理鼠标移动事件
                if event.type == pygame.MOUSEMOTION:
                    self.mouse_pos = event.pos
                
                # 处理鼠标按下事件
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键
                        self.mouse_pressed = True
                        self.mouse_clicked = True
                        self.mouse_held_time = 0
                    
                # 处理鼠标释放事件
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # 左键
                        self.mouse_pressed = False
                        self.mouse_released = True

                # 将事件传递给场景和精灵
                if self.scene:
                    self.scene.handle_event(event)
                    for sprite in self.scene.sprites:
                        sprite.handle_event(event)

            # 更新鼠标持续按下时间
            if self.mouse_pressed:
                self.mouse_held_time += self.clock.get_time()
        
            # 处理鼠标事件
            self.process_mouse_events()
        
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
                    
    def process_mouse_events(self):
        """处理鼠标事件"""
        # 处理按下事件
        if self.mouse_clicked:
            for obj, method, button, mode in self.mouse_events:
                if button == 1 and mode == "pressed":
                    self.add_task(method)
        
        # 处理释放事件
        if self.mouse_released:
            for obj, method, button, mode in self.mouse_events:
                if button == 1 and mode == "released":
                    self.add_task(method)
        
        # 处理按住事件（如果鼠标按住超过一帧）
        if self.mouse_pressed and self.mouse_held_time > 1000 / self.fps:
            for obj, method, button, mode in self.mouse_events:
                if button == 1 and mode == "held":
                    self.add_task(method)
    
    def setup_mouse_listeners(self, obj):
        """设置对象（场景或精灵）的鼠标监听器"""
        for name in dir(obj):
            method = getattr(obj, name)
            if callable(method) and hasattr(method, '_mouse_event'):
                button, mode = getattr(method, '_mouse_event')
                self.mouse_events.append((obj, method, button, mode))
                self.log_debug(
                    f"注册鼠标事件: 按钮{button} {mode} -> {obj.__class__.__name__}.{method.__name__}"
                )
    
    def mouse_x(self) -> int:
        """返回鼠标的x坐标"""
        return self.mouse_pos[0]
    
    def mouse_y(self) -> int:
        """返回鼠标的y坐标"""
        return self.mouse_pos[1]
    
    def mouse_is_down(self) -> bool:
        """检查鼠标是否按下"""
        return self.mouse_pressed
    
    def mouse_was_clicked(self) -> bool:
        """检查鼠标是否刚刚点击"""
        return self.mouse_clicked
    
    def mouse_was_released(self) -> bool:
        """检查鼠标是否刚刚释放"""
        return self.mouse_released
    
    def mouse_held_duration(self) -> int:
        """返回鼠标持续按下的时间（毫秒）"""
        return self.mouse_held_time

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
        self.background_size = None  # 背景图片尺寸 (width, height)
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

        # 收集按键、鼠标事件监听器
        if self.game:
            self.game.setup_key_listeners(self)
            self.game.setup_mouse_listeners(self)

    def set_background_image(self, image_path: str, size: Tuple[int, int] = None):
        """设置背景图片，并可选择缩放尺寸"""
        try:
            # 加载图片
            self.background_image = pygame.image.load(get_resource_path(image_path)).convert()
            
            # 如果指定了尺寸，缩放图片
            if size:
                self.background_size = size
                self.background_image = pygame.transform.scale(self.background_image, size)
            else:
                self.background_size = self.background_image.get_size()
                
            self.game.log_debug(f"Set background image: {image_path}")
        except Exception as e:
            self.game.log_debug(f"Failed to load background: {str(e)}")
            self.background_image = None
            self.background_size = None

    def set_background_size(self, width: int, height: int):
        """设置背景图片尺寸并缩放"""
        if self.background_image:
            self.background_size = (width, height)
            self.background_image = pygame.transform.scale(self.background_image, (width, height))

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
    
    def mouse_x(self) -> int:
        if self.game:
            return self.game.mouse_x()
        return 0
    
    def mouse_y(self) -> int:
        if self.game:
            return self.game.mouse_y()
        return 0
    
    def mouse_is_down(self) -> bool:
        if self.game:
            return self.game.mouse_is_down()
        return False
    
    def mouse_was_clicked(self) -> bool:
        if self.game:
            return self.game.mouse_was_clicked()
        return False
    
    def mouse_was_released(self) -> bool:
        if self.game:
            return self.game.mouse_was_released()
        return False
    
    def mouse_held_duration(self) -> int:
        if self.game:
            return self.game.mouse_held_duration()
        return 0

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
            # 如果有自定义尺寸，使用缩放后的图片
            if self.background_size:
                surface.blit(self.background_image, (0, 0))
            else:
                # 否则将图片平铺填满整个屏幕
                img_width, img_height = self.background_image.get_size()
                for y in range(0, self.game.height, img_height):
                    for x in range(0, self.game.width, img_width):
                        surface.blit(self.background_image, (x, y))
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
        self.costumes: Dict[str, pygame.Surface] = {}
        self.current_costume: str = None
        self._default_image: pygame.Surface = None

        self.color = (255, 100, 100)
        self.speech: str = None
        self.speech_timer = 0
        self.pen_down = False
        self.pen_color = (0, 0, 0)
        self.pen_size = 2
        self.pen_path = []
        self.collision_radius = 20.0 # 默认半径
        self.main_tasks = []
        self.clones_tasks = []
        self.broadcast_handlers = {}
        self.is_clones = False

        # --- 碰撞检测相关属性 ---
        self.collision_mask: Optional[pygame.mask.Mask] = None # 存储用于碰撞检测的mask
        self.edge_handlers: Dict[str, Callable] = {} # 存储碰到舞台边缘的事件处理函数
        self.sprite_collision_handlers: List[Tuple[Callable, Any]] = [] # 存储碰到其他精灵的事件处理函数
        
        self._collided_sprites: set = set() # 记录当前碰撞的精灵ID，以触发一次性事件
        self._last_on_edge: Optional[str] = None # 记录上次碰撞的边缘状态

        # 碰撞检测优化标志
        self.needs_edge_collision = False
        self.needs_sprite_collision = False
        
        # 添加移动状态变量
        self._is_moving = False
        self._active_movement = None

    # 新增的图片管理方法
    def add_costume(self, name: str, image: pygame.Surface):
        """添加一个造型"""
        self.costumes[name] = image
        if not self._default_image:
            self._default_image = image
        if self.current_costume is None:
            self.switch_costume(name)

    def next_costume(self):
        """切换到下一个造型"""
        keys = list(self.costumes.keys())
        if len(keys) < 2:
            return
        try:
            current_index = keys.index(self.current_costume)
            next_index = (current_index + 1) % len(keys)
            self.switch_costume(keys[next_index])
        except ValueError:
            self.switch_costume(keys[0])

    def switch_costume(self, name: str):
        """切换到指定名称的造型"""
        if name in self.costumes:
            self.current_costume = name
            self._update_collision_radius()

    def set_image(self, image: pygame.Surface):
        """设置当前使用的单个图像（向后兼容）"""
        self._default_image = image
        self.costumes = {}
        self.current_costume = None
        self._update_collision_radius()

    @property
    def image(self) -> Optional[pygame.Surface]:
        """获取当前使用的图像"""
        if self.current_costume and self.current_costume in self.costumes:
            return self.costumes[self.current_costume]
        return self._default_image

    def _update_collision_radius(self):
        """根据当前图像更新碰撞半径"""
        img = self.image
        if img:
            w, h = img.get_size()
            self.collision_radius = min(w, h) / 2.0
        else:
            self.collision_radius = 20.0 # 默认值

    def _create_mask(self):
        """(修正) 如果当前图像有alpha通道，创建并更新用于碰撞的mask"""
        img = self.image
        if img is None or not (img.get_flags() & pygame.SRCALPHA):
            self.collision_mask = None
            return

        # 缩放
        if self.size != 1.0:
            orig_size = img.get_size()
            new_size = (int(orig_size[0] * self.size), int(orig_size[1] * self.size))
            # 防止尺寸为0
            if new_size[0] <= 0 or new_size[1] <= 0:
                self.collision_mask = None
                return
            scaled_img = pygame.transform.scale(img, new_size)
        else:
            scaled_img = img

        # 旋转 (Pygame中，逆时针为正，而我们的方向系统是顺时针)
        # 90度是向上，所以需要调整
        rotated_img = pygame.transform.rotate(scaled_img, self.direction - 90)
        self.collision_mask = pygame.mask.from_surface(rotated_img)

    def main(self):
        pass

    def clones(self):
        pass

    def setup(self, scene: Scene):
        self.scene = scene
        self.game = scene.game
        self._update_collision_radius()

        if not self.game:
            return

        # --- (修正) 收集事件处理器并设置标志 ---
        # 收集@as_main, @as_clones, @handle_broadcast
        for name in dir(self):
            method = getattr(self, name)
            if not callable(method):
                continue
            if hasattr(method, '_is_main'):
                self.main_tasks.append(method)
            if hasattr(method, '_is_clones'):
                self.clones_tasks.append(method)
            if hasattr(method, '_broadcast_event'):
                event = getattr(method, '_broadcast_event')
                if event not in self.broadcast_handlers:
                    self.broadcast_handlers[event] = []
                self.broadcast_handlers[event].append(method)
            # 收集边缘碰撞处理器
            if hasattr(method, '_edge_collision'):
                edge = getattr(method, '_edge_collision')
                self.edge_handlers[edge] = method
            # 收集精灵碰撞处理器
            if hasattr(method, '_sprite_collisions'):
                for target in method._sprite_collisions:
                    self.sprite_collision_handlers.append((method, target))

        # (修正) 直接在此处设置优化标志
        self.needs_edge_collision = bool(self.edge_handlers)
        self.needs_sprite_collision = bool(self.sprite_collision_handlers)

        # --- 启动任务 ---
        if not self.is_clones:
            for task in self.main_tasks: self.game.add_task(task)
            if hasattr(self, 'main') and callable(self.main): self.game.add_task(self.main)
        else:
            for task in self.clones_tasks: self.game.add_task(task)
            if hasattr(self, 'clones') and callable(self.clones): self.game.add_task(self.clones)

        # 收集按键、鼠标事件监听器
        if self.game:
            self.game.setup_key_listeners(self)
            self.game.setup_mouse_listeners(self)

    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self):
        """(修正) 基础精灵更新逻辑"""
        if not self.game:
            return

        # (新增) 如果需要，更新碰撞mask
        if self.needs_sprite_collision:
            self._create_mask()

        if self.speech and self.speech_timer > 0:
            self.speech_timer -= self.game.clock.get_time()
            if self.speech_timer <= 0:
                self.speech = None

        # 执行必要的碰撞检测
        self._perform_collision_detection()

    def _perform_collision_detection(self):
        """(修正) 执行必要的碰撞检测"""
        # 1. 检测舞台边缘碰撞
        if self.needs_edge_collision:
            radius = self.collision_radius * self.size
            current_edge = None
            if self.pos.x - radius <= 0: current_edge = "left"
            elif self.pos.x + radius >= self.game.width: current_edge = "right"
            elif self.pos.y - radius <= 0: current_edge = "top"
            elif self.pos.y + radius >= self.game.height: current_edge = "bottom"
            
            if current_edge != self._last_on_edge:
                if current_edge:
                    self._on_edge_collision(current_edge)
                self._last_on_edge = current_edge

        # 2. 检测精灵间碰撞
        if self.needs_sprite_collision and self.scene:
            current_frame_collisions = set()
            for other in self.scene.sprites:
                if other is self or not other.visible:
                    continue

                if self.collides_with(other):
                    current_frame_collisions.add(id(other))
                    if id(other) not in self._collided_sprites:
                        # 碰撞发生，现在检查哪个处理器对这个'other'感兴趣
                        for handler, target in self.sprite_collision_handlers:
                            is_match = (target is None or
                                        (isinstance(target, str) and other.name == target) or
                                        (isinstance(target, type) and isinstance(other, target)))
                            if is_match:
                                self._trigger_sprite_collision_handler(handler, other)
            self._collided_sprites = current_frame_collisions
            
    def mouse_x(self) -> int:
        return self.game.mouse_x() if self.game else 0
    
    def mouse_y(self) -> int:
        return self.game.mouse_y() if self.game else 0
    
    def mouse_is_down(self) -> bool:
        return self.game.mouse_is_down() if self.game else False
    
    def mouse_was_clicked(self) -> bool:
        return self.game.mouse_was_clicked() if self.game else False
    
    def mouse_was_released(self) -> bool:
        return self.game.mouse_was_released() if self.game else False
    
    def mouse_held_duration(self) -> int:
        return self.game.mouse_held_duration() if self.game else 0
    
    def touches_mouse(self) -> bool:
        """检查精灵是否碰到鼠标"""
        if not self.game or not self.visible:
            return False
            
        mouse_x, mouse_y = self.game.mouse_pos
        distance_sq = (self.pos.x - mouse_x)**2 + (self.pos.y - mouse_y)**2
        radius = self.collision_radius * self.size
        return distance_sq <= radius**2
    
    def distance_to_mouse(self) -> float:
        """返回精灵到鼠标的距离"""
        if not self.game: return 0
        return self.pos.distance_to(self.game.mouse_pos)
    
    def go_to_mouse(self):
        """立即移动到鼠标位置"""
        if self.game: self.pos.update(self.game.mouse_pos)
    
    def glide_to_mouse(self, duration: float = 1000, easing: str = "linear"):
        """平滑移动到鼠标位置"""
        if not self.game: return
        target_pos = pygame.Vector2(self.game.mouse_pos)
        yield from self.glide_to(target_pos.x, target_pos.y, duration, easing)

    def broadcast(self, event_name: str):
        if self.scene: self.scene.broadcast(event_name)

    def received_broadcast(self, event_name: str) -> bool:
        return self.game.received_broadcast(event_name) if self.game else False

    def collides_with(self, other: "Sprite") -> bool:
        """(修正) 检查两个精灵是否碰撞 (Mask优先)"""
        if not self.visible or not other.visible:
            return False

        # 优先使用mask碰撞检测
        # (修正) 确保另一个精灵也有mask
        if self.collision_mask and other.collision_mask:
            offset_x = int(other.pos.x - other.collision_mask.get_rect().width / 2) - \
                       int(self.pos.x - self.collision_mask.get_rect().width / 2)
            offset_y = int(other.pos.y - other.collision_mask.get_rect().height / 2) - \
                       int(self.pos.y - self.collision_mask.get_rect().height / 2)
            
            return self.collision_mask.overlap(other.collision_mask, (offset_x, offset_y)) is not None

        # 后备：圆形碰撞检测
        my_radius = self.collision_radius * self.size
        other_radius = other.collision_radius * other.size
        distance_sq = self.pos.distance_squared_to(other.pos)
        return distance_sq < (my_radius + other_radius)**2

    def _on_edge_collision(self, edge: str):
        """触发碰到舞台边缘事件"""
        if self.game:
            self.game.log_debug(f"Edge collision: {self.name} hit {edge} border")
        
        # 触发通用处理器
        if "any" in self.edge_handlers:
            self.game.add_task(self.edge_handlers["any"])
        # 触发特定处理器
        if edge in self.edge_handlers:
            self.game.add_task(self.edge_handlers[edge])

    def _trigger_sprite_collision_handler(self, handler: Callable, other: "Sprite"):
        """(新增) 根据处理器签名，安全地将任务添加到游戏循环中"""
        sig = inspect.signature(handler)
        if 'other' in sig.parameters:
            task_to_add = lambda: handler(other)
        else:
            task_to_add = handler
        self.game.add_task(task_to_add)

    def touches_color(self, color: Tuple[int, int, int], tolerance: int = 0) -> bool:
        """
        检查精灵边缘是否触碰到指定颜色。
        注意：此操作性能开销较大，请谨慎使用。
        """
        if not self.game or not self.visible:
            return False
            
        edge_points = self._get_edge_points()
        for point in edge_points:
            if self._point_touches_color(point, color, tolerance):
                return True
        return False
        
    def _get_edge_points(self) -> List[Tuple[int, int]]:
        """获取精灵边缘的点（用于颜色碰撞检测）"""
        # ... 此方法逻辑正确但性能开销大，保持不变 ...
        points = []
        center_x, center_y = int(self.pos.x), int(self.pos.y)
        
        # 如果有mask，使用其轮廓
        if self.collision_mask:
            rect = self.collision_mask.get_rect(center=(center_x, center_y))
            # 每隔5个点取一个以提高性能
            for i, p in enumerate(self.collision_mask.outline()):
                if i % 5 == 0:
                    points.append((p[0] + rect.x, p[1] + rect.y))
        # 否则使用圆形轮廓
        else:
            radius = int(self.collision_radius * self.size)
            for angle in range(0, 360, 15): # 增加步长以提高性能
                rad = math.radians(angle)
                x = center_x + radius * math.cos(rad)
                y = center_y - radius * math.sin(rad) # Pygame Y轴向下
                points.append((int(x), int(y)))
        return points
        
    def _point_touches_color(self, point: Tuple[int, int], 
                             target_color: Tuple[int, int, int], 
                             tolerance: int) -> bool:
        """检查特定点是否触碰到目标颜色"""
        x, y = point
        if not (0 <= x < self.game.width and 0 <= y < self.game.height):
            return False
            
        try:
            screen_color = self.game.screen.get_at((x, y))
        except IndexError:
            return False
            
        return self._colors_match(screen_color[:3], target_color, tolerance)
        
    def _colors_match(self, color1: Tuple[int, int, int], 
                      color2: Tuple[int, int, int], 
                      tolerance: int) -> bool:
        """检查两个颜色是否在容差范围内匹配"""
        return (abs(color1[0] - color2[0]) <= tolerance and
                abs(color1[1] - color2[1]) <= tolerance and
                abs(color1[2] - color2[2]) <= tolerance)

    def set_size(self, size: float):
        self.size = max(0.01, size) # 防止尺寸为0
        self._update_collision_radius()

    def change_size(self, change: float):
        self.set_size(self.size + change)

    def move(self, steps: float):
        """移动精灵，无物理效果"""
        rad = math.radians(self.direction)
        dx = steps * math.cos(rad)
        dy = -steps * math.sin(rad)
        new_pos = self.pos + pygame.Vector2(dx, dy)

        if self.pen_down:
            self.pen_path.append(self.pos.xy)
            self.pos.update(new_pos)
            self.pen_path.append(self.pos.xy)
        else:
            self.pos.update(new_pos)
    
    def move_left(self, distance: float, prevent_boundary: bool = True):
        """向左移动指定距离"""
        new_x = self.pos.x - distance
        if prevent_boundary and self.game:
            radius = self.collision_radius * self.size
            new_x = max(radius, new_x)
        self.pos.x = new_x
        if self.pen_down: self.pen_path.append(self.pos.xy)

    def move_right(self, distance: float, prevent_boundary: bool = True):
        """向右移动指定距离"""
        new_x = self.pos.x + distance
        if prevent_boundary and self.game:
            radius = self.collision_radius * self.size
            new_x = min(self.game.width - radius, new_x)
        self.pos.x = new_x
        if self.pen_down: self.pen_path.append(self.pos.xy)

    def move_up(self, distance: float, prevent_boundary: bool = True):
        """向上移动指定距离"""
        new_y = self.pos.y - distance
        if prevent_boundary and self.game:
            radius = self.collision_radius * self.size
            new_y = max(radius, new_y)
        self.pos.y = new_y
        if self.pen_down: self.pen_path.append(self.pos.xy)

    def move_down(self, distance: float, prevent_boundary: bool = True):
        """向下移动指定距离"""
        new_y = self.pos.y + distance
        if prevent_boundary and self.game:
            radius = self.collision_radius * self.size
            new_y = min(self.game.height - radius, new_y)
        self.pos.y = new_y
        if self.pen_down: self.pen_path.append(self.pos.xy)

    def turn_right(self, degrees: float):
        self.direction = (self.direction - degrees) % 360

    def turn_left(self, degrees: float):
        self.direction = (self.direction + degrees) % 360

    def point_in_direction(self, degrees: float):
        self.direction = degrees % 360

    def point_towards(self, x: float, y: float):
        dx = x - self.pos.x
        dy = self.pos.y - y
        self.direction = math.degrees(math.atan2(dy, dx)) % 360

    
    def glide_to(self, target_x: float, target_y: float, duration: float = 1000,easing: str = "linear"):
        """在指定时间内平滑移动到目标位置"""
        if not self.game or duration <= 0:
            self.pos.update(target_x, target_y)
            return

        start_pos = self.pos.copy()
        target_pos = pygame.Vector2(target_x, target_y)
        start_time = self.game.current_time
        end_time = start_time + duration
        
        while self.game.current_time < end_time:
            progress = (self.game.current_time - start_time) / duration
            
            if easing == "ease_in_out":
                t = progress * progress * (3 - 2 * progress)
            elif easing == "ease_in":
                t = progress * progress
            elif easing == "ease_out":
                t = 1 - (1 - progress) * (1 - progress)
            else: # linear
                t = progress
            
            self.pos = start_pos.lerp(target_pos, t)
            yield 0
        
        self.pos.update(target_pos)
    
    
    def glide_in_direction(self, direction: float, distance: float, 
                           duration: float = 1000, easing: str = "linear",
                           exclusive: bool = True):
        """向指定方向平滑移动指定距离"""
        rad = math.radians(direction)
        delta = pygame.Vector2(math.cos(rad), -math.sin(rad)) * distance
        target_pos = self.pos + delta
        
        # 互斥逻辑
        if exclusive and self._is_moving:
            if self._is_conflicting_movement(direction):
                return
        
        self._is_moving = True
        self._active_movement = self._get_movement_type(direction)
        
        yield from self.glide_to(target_pos.x, target_pos.y, duration, easing)
        
        self._is_moving = False
        self._active_movement = None
    
    def _get_movement_type(self, direction: float) -> str:
        """获取移动方向类型"""
        d = direction % 360
        if 315 <= d or d < 45: return "right"
        if 45 <= d < 135: return "up"
        if 135 <= d < 225: return "left"
        return "down"
    
    def _is_conflicting_movement(self, new_direction: float) -> bool:
        """检查新移动是否与当前活动移动冲突"""
        if not self._active_movement: return False
        new_type = self._get_movement_type(new_direction)
        opposites = {"left": "right", "right": "left", "up": "down", "down": "up"}
        return opposites.get(self._active_movement) == new_type

    def glide_left(self, distance: float, duration: float = 1000, easing: str = "linear", exclusive: bool = True):
        yield from self.glide_in_direction(180, distance, duration, easing, exclusive)

    def glide_right(self, distance: float, duration: float = 1000, easing: str = "linear", exclusive: bool = True):
        yield from self.glide_in_direction(0, distance, duration, easing, exclusive)

    def glide_up(self, distance: float, duration: float = 1000, easing: str = "linear", exclusive: bool = True):
        yield from self.glide_in_direction(90, distance, duration, easing, exclusive)

    def glide_down(self, distance: float, duration: float = 1000, easing: str = "linear", exclusive: bool = True):
        yield from self.glide_in_direction(270, distance, duration, easing, exclusive)

    def goto(self, x: float, y: float):
        self.pos.update(x, y)

    def goto_random_position(self):
        if not self.game: return
        radius = self.collision_radius * self.size
        self.pos.x = random.uniform(radius, self.game.width - radius)
        self.pos.y = random.uniform(radius, self.game.height - radius)

    def say(self, text: str, duration: int = 2000):
        self.speech = text
        self.speech_timer = duration

    def think(self, text: str, duration: int = 2000):
        self.say(text, duration)

    def change_color_to(self, color: Tuple[int, int, int]):
        self.color = color

    def change_color_random(self):
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def clone(self, other_sprite: 'Sprite' = None):
        """克隆精灵"""
        if not self.scene or not self.game or len(self.scene.sprites) >= 500:
            return

        source = other_sprite if other_sprite else self
        clone = type(source)() # 创建同类型的实例

        # 复制属性
        clone.pos = source.pos.copy()
        clone.direction = source.direction
        clone.size = source.size
        clone.color = source.color
        clone.costumes = source.costumes.copy()
        clone.current_costume = source.current_costume
        clone._default_image = source._default_image
        clone.visible = source.visible
        clone.is_clones = True

        self.scene.add_sprite(clone)
        self.game.log_debug(f"Cloned sprite: {source.name}")

    def delete_self(self):
        self.delete = True

    def pen_down(self):
        self.pen_down = True
        self.pen_path.append(self.pos.xy)

    def pen_up(self):
        self.pen_down = False
        self.pen_path.clear() # 或者根据需要不清空

    def change_pen_color(self, color: Tuple[int, int, int]):
        self.pen_color = color

    def set_pen_color_random(self):
        self.pen_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def change_pen_size(self, size: int):
        self.pen_size = max(1, size)

    def clear_pen(self):
        # 这个方法应该在场景层面实现，因为它需要清除所有精灵的轨迹
        if self.scene:
            # 这是一个示例，实际可能需要一个全局的画板
            for s in self.scene.sprites:
                s.pen_path = []

    def face_towards(self, target: Any):
        """让精灵面向特定目标"""
        if isinstance(target, str):
            if target == "mouse":
                if self.game: self.point_towards(*self.game.mouse_pos)
                return
            if target == "edge":
                if not self.game: return
                distances = {
                    "left": self.pos.x, "right": self.game.width - self.pos.x,
                    "top": self.pos.y, "bottom": self.game.height - self.pos.y,
                }
                closest_edge = min(distances, key=distances.get)
                if closest_edge == "left": self.point_towards(0, self.pos.y)
                elif closest_edge == "right": self.point_towards(self.game.width, self.pos.y)
                elif closest_edge == "top": self.point_towards(self.pos.x, 0)
                else: self.point_towards(self.pos.x, self.game.height)
                return
            
            # 按名称查找精灵
            if self.scene:
                for sprite in self.scene.sprites:
                    if sprite.name == target:
                        self.point_towards(sprite.pos.x, sprite.pos.y)
                        return
        elif isinstance(target, Sprite):
            self.point_towards(target.pos.x, target.pos.y)
        elif isinstance(target, (pygame.Vector2, tuple)):
            self.point_towards(*target)

    def face_random_direction(self):
        self.direction = random.uniform(0, 360)

    def face_horizontal(self, degrees: float = 0):
        self.point_in_direction(degrees)

    def face_vertical(self, degrees: float = 90):
        self.point_in_direction(degrees)

    def face_away_from(self, target: Any):
        """背向特定目标"""
        self.face_towards(target)
        self.direction = (self.direction + 180) % 360

    def draw(self, surface: pygame.Surface):
        """绘制精灵"""
        if not self.visible: return
        
        # 绘制画笔轨迹
        if self.pen_path and len(self.pen_path) >= 2:
            pygame.draw.lines(surface, self.pen_color, False, self.pen_path, self.pen_size)

        # 绘制精灵主体
        img_to_draw = self.image
        if img_to_draw:
            scaled_img = pygame.transform.scale(img_to_draw, (int(img_to_draw.get_width() * self.size), int(img_to_draw.get_height() * self.size))) if self.size != 1.0 else img_to_draw
            rotated_image = pygame.transform.rotate(scaled_img, self.direction - 90)
            rect = rotated_image.get_rect(center=self.pos)
            surface.blit(rotated_image, rect)
        else:
            radius = int(self.collision_radius * self.size)
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), radius)
            rad = math.radians(self.direction)
            end_pos = self.pos + pygame.Vector2(math.cos(rad), -math.sin(rad)) * radius
            pygame.draw.line(surface, (0, 0, 0), self.pos, end_pos, 2)

        # 绘制说话气泡
        if self.speech and self.game:
            text = self.game.font.render(self.speech, True, (0, 0, 0))
            bubble_rect = text.get_rect(center=(self.pos.x, self.pos.y - 50)).inflate(20, 15)
            pygame.draw.rect(surface, (255, 255, 200), bubble_rect, border_radius=10)
            pygame.draw.rect(surface, (200, 200, 100), bubble_rect, 2, border_radius=10)
            # 绘制小三角
            p1 = bubble_rect.midbottom
            p2 = (p1[0] - 10, p1[1] + 10)
            p3 = (p1[0] + 10, p1[1] + 10)
            pygame.draw.polygon(surface, (255, 255, 200), (p1, p2, p3))
            pygame.draw.polygon(surface, (200, 200, 100), (p1, p2, p3), 2)
            surface.blit(text, text.get_rect(center=bubble_rect.center))

    def play_sound(self, name: str, volume: float = None):
        if self.game: self.game.play_sound(name, volume)
    
    def play_music(self, name: str, loops: int = -1, volume: float = None):
        if self.game: self.game.play_music(name, loops, volume)
    
    def play_drum(self, drum_type: str, duration: int = 100):
        if self.game: self.game.play_drum(drum_type, duration)
    
    def play_note(self, note: str, duration: int = 500):
        if self.game: self.game.play_note(note, duration)
    
    def stop_music(self):
        if self.game: self.game.stop_music()
    
    def set_music_volume(self, volume: float):
        if self.game: self.game.set_music_volume(volume)
    
    def set_sound_volume(self, volume: float):
        if self.game: self.game.set_sound_volume(volume)

class Cat(Sprite):

    def __init__(self):
        super().__init__()
        self.name = "Cat"
        # 确保资源文件存在
        try:
            self.add_costume("costume1", pygame.image.load(get_resource_path("cat1.svg")).convert_alpha())
            self.add_costume("costume2", pygame.image.load(get_resource_path("cat2.svg")).convert_alpha())
        except pygame.error as e:
            print(f"无法加载Cat资源: {e}. 将使用默认圆形。")


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
        self.show_speed_surf = False

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
        radius = self.collision_radius * self.size

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

        # 绘制速度矢量
        if self.show_speed_surf and self.velocity.length() > 0.1:
            end_vx = self.pos.x + self.velocity.x * 10
            end_vy = self.pos.y + self.velocity.y * 10
            pygame.draw.line(surface, (255, 0, 0), self.pos, (end_vx, end_vy), 2)

            # 在箭头处绘制速度值
            speed = self.velocity.length()
            speed_text = f"{speed:.1f}"
            speed_surf = self.game.font.render(speed_text, True, (255, 0, 0))
            surface.blit(speed_surf, (end_vx + 5, end_vy - 10))