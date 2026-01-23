"""
AI Service

Handles AI API calls for code assistance.
"""

import json
import os
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QThread

from .settings import Settings


@dataclass
class Message:
    """Chat message."""
    role: str  # "system", "user", "assistant"
    content: str


class AIWorker(QThread):
    """Worker thread for AI API calls."""

    response_chunk = Signal(str)
    response_done = Signal()
    error_occurred = Signal(str)

    def __init__(self, endpoint: str, api_key: str, model: str, messages: List[Dict]):
        super().__init__()
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.messages = messages

    def run(self):
        """Execute API call."""
        try:
            import urllib.request
            import urllib.error

            url = f"{self.endpoint}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": self.model,
                "messages": self.messages,
                "stream": True
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                for line in response:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                self.response_chunk.emit(content)
                        except json.JSONDecodeError:
                            pass

            self.response_done.emit()

        except urllib.error.HTTPError as e:
            self.error_occurred.emit(f"HTTP Error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            self.error_occurred.emit(f"Connection Error: {e.reason}")
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")


class AIService(QObject):
    """AI service for code assistance."""

    response_chunk = Signal(str)
    response_done = Signal()
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = Settings()
        self._worker: Optional[AIWorker] = None
        self._messages: List[Message] = []
        self._engine_source = ""

    def load_engine_source(self, engine_path: str):
        """Load scrawl engine source code."""
        try:
            with open(engine_path, "r", encoding="utf-8") as f:
                self._engine_source = f.read()
        except Exception:
            self._engine_source = ""

    def get_system_prompt(self, context: str = "") -> str:
        """Build system prompt with engine source and context."""
        engine_src = self._engine_source[:30000] if self._engine_source else "未加载"

        prompt = f"""你是Scrawl游戏引擎的AI编程助手。帮助用户编写和修改游戏代码。

Scrawl引擎源码：
```python
{engine_src}
```

## 代码修改格式
当你需要修改精灵或场景的代码时，请使用以下格式：

修改精灵代码：
```python:sprite:精灵名称或ID
# 完整的精灵代码
class MySprite(Sprite):
    ...
```

修改场景代码：
```python:scene:场景名称或ID
# 完整的场景代码
class MyScene(Scene):
    ...
```

注意：
- 必须提供完整的代码，不是代码片段
- 使用精灵/场景的名称或ID作为目标
- 用户点击"应用"按钮后代码会自动更新到对应的精灵/场景

## 属性修改格式
当你需要修改精灵或场景的属性时，请使用JSON格式：

修改精灵属性：
```json:sprite:精灵名称或ID
"""
        # Add JSON examples without f-string to avoid brace issues
        prompt += '{\n    "name": "新名称",\n    "x": 100,\n    "y": 200,\n'
        prompt += '    "size": 1.0,\n    "direction": 0,\n    "visible": true,\n'
        prompt += '    "is_physics": false\n}\n```\n\n'

        prompt += '修改场景属性：\n```json:scene:场景名称或ID\n'
        prompt += '{\n    "name": "新场景名",\n    "bg_color": "#336699"\n}\n```\n\n'

        prompt += '修改游戏设置：\n```json:game:settings\n'
        prompt += '{\n    "title": "游戏标题",\n    "width": 800,\n    "height": 600,\n'
        prompt += '    "fps": 60,\n    "fullscreen": false,\n    "debug": false\n}\n```\n\n'

        prompt += "注意：只需包含要修改的属性，不需要包含所有属性。\n\n"

        # Add Scrawl API documentation
        prompt += self._get_api_documentation()

        if context:
            prompt += f"\n当前项目上下文：\n{context}\n"

        prompt += "\n请用中文回答，代码要简洁清晰。"
        return prompt

    def send_message(self, user_message: str, context: str = ""):
        """Send message to AI."""
        api_key = self._settings.get_ai_api_key()
        if not api_key:
            self.error_occurred.emit("请先在设置中配置API Key")
            return

        # Add user message
        self._messages.append(Message("user", user_message))

        # Build messages for API
        messages = [{"role": "system", "content": self.get_system_prompt(context)}]
        for msg in self._messages[-10:]:  # Keep last 10 messages
            messages.append({"role": msg.role, "content": msg.content})

        # Start worker
        self._worker = AIWorker(
            self._settings.get_ai_endpoint(),
            api_key,
            self._settings.get_ai_model(),
            messages
        )
        self._worker.response_chunk.connect(self.response_chunk.emit)
        self._worker.response_done.connect(self._on_response_done)
        self._worker.error_occurred.connect(self.error_occurred.emit)
        self._worker.start()

    def _on_response_done(self):
        """Handle response completion."""
        self.response_done.emit()

    def add_assistant_message(self, content: str):
        """Add assistant response to history."""
        self._messages.append(Message("assistant", content))

    def clear_history(self):
        """Clear chat history."""
        self._messages.clear()

    def is_busy(self) -> bool:
        """Check if AI is processing."""
        return self._worker is not None and self._worker.isRunning()

    def _get_api_documentation(self) -> str:
        """Get complete Scrawl engine API documentation."""
        doc = """## Scrawl引擎完整API文档

### 重要提示
- **IDE可配置的属性（name, x, y, size, direction, visible, is_physics等）不需要在__init__中显式设置**
- 如果需要修改这些属性，请使用上面的JSON属性修改格式（```json:sprite:名称```），而不是在代码的__init__中设置
- 只有IDE无法配置的属性（如自定义变量、速度等）才需要在__init__中初始化

### Sprite类核心属性
| 属性 | 类型 | 说明 |
|------|------|------|
| self.pos | pygame.Vector2 | 位置，用self.pos.x和self.pos.y访问 |
| self.direction | float | 方向角度（0=右，90=上，180=左，270=下） |
| self.size | float | 缩放比例（1.0=原始大小） |
| self.visible | bool | 是否可见 |
| self.name | str | 精灵名称 |
| self.color | tuple | RGB颜色，如(255, 0, 0) |
| self.collision_type | str | 碰撞类型："rect"/"circle"/"mask" |

**注意：没有self.x和self.y属性！必须使用self.pos.x和self.pos.y**

### PhysicsSprite额外属性（继承自Sprite）
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| self.velocity | pygame.Vector2 | (0, 0) | 速度向量 |
| self.gravity | pygame.Vector2 | (0, 0.2) | 重力向量 |
| self.friction | float | 0.02 | 摩擦力系数(0-1) |
| self.elasticity | float | 0.8 | 弹性系数 |

"""
        doc += self._get_movement_api()
        doc += self._get_direction_api()
        doc += self._get_mouse_api()
        doc += self._get_collision_api()
        doc += self._get_costume_api()
        doc += self._get_sound_api()
        doc += self._get_pen_api()
        doc += self._get_other_api()
        doc += self._get_decorator_api()
        doc += self._get_code_examples()
        return doc

    def _get_movement_api(self) -> str:
        """Get movement API documentation."""
        return """
### 移动方法
| 方法 | 说明 |
|------|------|
| self.move(steps) | 向当前方向移动steps步 |
| self.move_left(dist) | 向左移动dist像素 |
| self.move_right(dist) | 向右移动dist像素 |
| self.move_up(dist) | 向上移动dist像素 |
| self.move_down(dist) | 向下移动dist像素 |
| self.go_to(x, y) | 瞬间移动到(x, y) |
| self.go_to_random_position() | 移动到随机位置 |
| yield from self.glide_to(x, y, duration, easing) | 滑行到(x, y)，duration毫秒 |
| yield from self.glide_left(dist, duration) | 向左滑行 |
| yield from self.glide_right(dist, duration) | 向右滑行 |
| yield from self.glide_up(dist, duration) | 向上滑行 |
| yield from self.glide_down(dist, duration) | 向下滑行 |

easing可选值: "linear", "ease_in", "ease_out", "ease_in_out"

"""

    def _get_direction_api(self) -> str:
        """Get direction API documentation."""
        return """
### 方向方法
| 方法 | 说明 |
|------|------|
| self.turn_left(deg) | 左转deg度 |
| self.turn_right(deg) | 右转deg度 |
| self.point_in_direction(deg) | 设置方向为deg度 |
| self.point_towards(x, y) | 面向坐标(x, y) |
| self.face_towards(target) | 面向目标（"mouse"/"edge"/精灵名/Sprite对象） |
| self.face_away_from(target) | 背向目标 |
| self.face_random_direction() | 随机方向 |

"""

    def _get_mouse_api(self) -> str:
        """Get mouse API documentation."""
        return """
### 鼠标方法
| 方法 | 说明 |
|------|------|
| self.mouse_x() | 获取鼠标X坐标 |
| self.mouse_y() | 获取鼠标Y坐标 |
| self.is_mouse_down() | 鼠标是否按下 |
| self.is_mouse_clicked() | 鼠标是否刚点击 |
| self.is_mouse_released() | 鼠标是否刚释放 |
| self.is_touching_mouse() | 是否触碰鼠标 |
| self.distance_to_mouse() | 到鼠标的距离 |
| self.go_to_mouse() | 移动到鼠标位置 |
| yield from self.glide_to_mouse(duration) | 滑行到鼠标位置 |

"""

    def _get_collision_api(self) -> str:
        """Get collision API documentation."""
        return """
### 碰撞方法
| 方法 | 说明 |
|------|------|
| self.is_colliding_with(other_sprite) | 是否与另一精灵碰撞 |
| self.is_touching_color(color, tolerance) | 是否触碰指定颜色 |
| self.set_collision_type(mode) | 设置碰撞类型："rect"/"circle"/"mask" |
| self.get_rect() | 获取精灵矩形区域 |

"""

    def _get_costume_api(self) -> str:
        """Get costume API documentation."""
        return """
### 造型方法
| 方法 | 说明 |
|------|------|
| self.add_costume(name, image) | 添加造型 |
| self.switch_costume(name) | 切换到指定造型 |
| self.next_costume() | 切换到下一个造型 |
| self.set_image(image) | 设置默认图像 |

"""

    def _get_sound_api(self) -> str:
        """Get sound API documentation."""
        return """
### 声音方法
| 方法 | 说明 |
|------|------|
| self.play_sound(name, volume) | 播放音效 |
| self.play_music(name, loops, volume) | 播放背景音乐(loops=-1循环) |
| self.stop_music() | 停止背景音乐 |
| self.play_note(note, duration) | 播放音符(C4-C5) |
| self.play_drum(type, duration) | 播放鼓声(bass/snare/hihat/cymbal) |
| self.set_music_volume(volume) | 设置音乐音量(0.0-1.0) |
| self.set_sound_volume(volume) | 设置音效音量(0.0-1.0) |

"""

    def _get_pen_api(self) -> str:
        """Get pen API documentation."""
        return """
### 画笔方法
| 方法 | 说明 |
|------|------|
| self.put_pen_down() | 落笔 |
| self.put_pen_up() | 抬笔 |
| self.set_pen_color(color) | 设置画笔颜色 |
| self.set_pen_color_random() | 随机画笔颜色 |
| self.set_pen_size(size) | 设置画笔粗细 |
| self.clear_pen() | 清除画笔轨迹 |

"""

    def _get_other_api(self) -> str:
        """Get other API documentation."""
        return """
### 其他方法
| 方法 | 说明 |
|------|------|
| self.say(text, duration) | 显示对话气泡 |
| self.think(text, duration) | 显示思考气泡 |
| self.set_size(size) | 设置大小 |
| self.change_size(change) | 改变大小 |
| self.set_color(color) | 设置颜色 |
| self.set_color_random() | 随机颜色 |
| self.clone() | 克隆自己 |
| self.clone(other_sprite) | 克隆其他精灵 |
| self.delete_self() | 删除自己 |
| self.broadcast(event_name) | 广播事件 |
| self.received_broadcast(event_name) | 是否收到广播 |

"""

    def _get_decorator_api(self) -> str:
        """Get decorator API documentation."""
        return """
### 装饰器（用于事件处理）
```python
@as_main
def main_loop(self):
    \"\"\"主循环，游戏开始时自动执行\"\"\"
    while True:
        # 游戏逻辑
        yield 0  # 每帧执行

@as_clones
def clones_loop(self):
    \"\"\"克隆体循环，克隆时自动执行\"\"\"
    while True:
        yield 0

@on_key(pygame.K_SPACE, "pressed")
def on_space(self):
    \"\"\"按下空格键时触发\"\"\"
    yield

@on_key(pygame.K_UP, "down")
def on_up_held(self):
    \"\"\"按住上键时持续触发\"\"\"
    yield

@on_mouse("clicked", 1)
def on_click(self):
    \"\"\"鼠标左键点击时触发\"\"\"
    yield

@on_sprite_clicked
def on_self_clicked(self):
    \"\"\"精灵被点击时触发\"\"\"
    yield

@on_broadcast("game_over")
def on_game_over(self):
    \"\"\"收到game_over广播时触发\"\"\"
    yield

@on_edge_collision("any")
def on_hit_edge(self):
    \"\"\"碰到任意边缘时触发（可选：left/right/top/bottom）\"\"\"
    yield

@on_sprite_collision(OtherSprite)
def on_hit_other(self, other):
    \"\"\"碰到OtherSprite类型精灵时触发\"\"\"
    yield
```

"""

    def _get_code_examples(self) -> str:
        """Get code examples."""
        return """
### 代码示例

#### 键盘控制移动（推荐方式）
```python
class Player(Sprite):
    @as_main
    def main_loop(self):
        while True:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.pos.x -= 5
            if keys[pygame.K_RIGHT]:
                self.pos.x += 5
            if keys[pygame.K_UP]:
                self.pos.y -= 5
            if keys[pygame.K_DOWN]:
                self.pos.y += 5
            yield 0
```

#### 使用内置移动方法
```python
class Player(Sprite):
    @as_main
    def main_loop(self):
        while True:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.move_left(5)
            if keys[pygame.K_RIGHT]:
                self.move_right(5)
            yield 0
```

#### 物理精灵示例
```python
class Ball(PhysicsSprite):
    # 不需要在__init__中设置pos/size等，IDE会配置

    @as_main
    def main_loop(self):
        # 可以修改物理属性
        self.gravity = pygame.Vector2(0, 0.5)
        self.elasticity = 0.9
        while True:
            yield 0
```

"""
