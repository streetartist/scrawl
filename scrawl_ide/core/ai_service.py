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
                            choices = chunk.get("choices", [])
                            if choices and len(choices) > 0:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    self.response_chunk.emit(content)
                        except (json.JSONDecodeError, IndexError):
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

    # Free models configuration
    FREE_ENDPOINT = "https://aihubmix.com/v1"
    FREE_API_KEY = "sk-W1ZDyW5rbKBFPFRNEd1a3d934cD249B4B5094e1aBa6e7610"
    FREE_MODELS = [
        ("gemini-2.0-flash-free", "Gemini 2.0 Flash"),
        ("gemini-3-flash-preview-free", "Gemini 3 Flash"),
        ("glm-4.7-flash-free", "GLM 4.7 Flash"),
        ("coding-glm-4.7-free", "Coding GLM 4.7"),
        ("coding-minimax-m2.1-free", "Coding MiniMax"),
        ("kimi-for-coding-free", "Kimi Coding"),
        ("mimo-v2-flash-free", "Mimo V2 Flash"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = Settings()
        self._worker: Optional[AIWorker] = None
        self._messages: List[Message] = []
        self._engine_source = ""
        # Custom config (None means use settings)
        self._custom_endpoint: Optional[str] = None
        self._custom_api_key: Optional[str] = None
        self._custom_model: Optional[str] = None

    def set_custom_config(self, endpoint: Optional[str], api_key: Optional[str], model: Optional[str]):
        """Set custom endpoint, API key and model. Pass None to use settings."""
        self._custom_endpoint = endpoint
        self._custom_api_key = api_key
        self._custom_model = model

    def get_current_config(self) -> tuple:
        """Get current endpoint, api_key, model."""
        if self._custom_endpoint is not None:
            return (self._custom_endpoint, self._custom_api_key, self._custom_model)
        return (
            self._settings.get_ai_endpoint(),
            self._settings.get_ai_api_key(),
            self._settings.get_ai_model()
        )

    def load_engine_source(self, engine_path: str):
        """Load scrawl engine source code."""
        try:
            with open(engine_path, "r", encoding="utf-8") as f:
                self._engine_source = f.read()
        except Exception:
            self._engine_source = ""

    def get_system_prompt(self, context: str = "") -> str:
        """Build system prompt with engine source and context."""
        prompt = """你是Scrawl IDE的AI编程助手。帮助用户在IDE中编写游戏代码。

## 核心思维链（CoT）
**在生成代码前，请先思考：**
1. 用户的需求是什么？
2. 是静态配置（精灵属性/造型）还是动态逻辑（移动/事件）？
3. **坐标计算**：注意 (0,0) 是屏幕左上角，但**精灵坐标 (x,y) 是精灵的中心点**！
   - 例如：放置在左上角的按钮(宽100,高50)，坐标应设为 x=50, y=25 (而不是 0,0)。
4. **关键判断**：除了scrawl/pygame，是否需要导入其他库（如math, random）？
4. **安全检查**：
   - 是否定义了 `__init__` 并调用 `super().__init__()`？（**必须**）
   - 是否有循环阻塞？

## 🚫 严禁事项（Forbidden Patterns）
1. **禁止在代码中加载资源**：严禁使用 `pygame.image.load()`。所有造型**必须**通过IDE属性（JSON格式）添加。
2. **禁止修改IDE托管属性**：`self.x`, `self.y`, `self.rect` 是IDE管理的。代码中**只读**，修改请用API（`self.pos.x`, `self.move`）。
3. **禁止阻塞主线程**：严禁 `time.sleep()`。必须用 `yield`。
4. **禁止自定义字体**：优先使用 `self.game.font`，不要用 `pygame.font.SysFont`，以保持风格统一。
5. **禁止省略 __init__**：必须显示定义 `__init__` 并调用 `super().__init__()`。这是**强制要求**，否则会出问题。

## ✅ 正确工作流
1. **添加造型**：
   - **图片造型**：使用JSON格式 `"costumes": [...]`
   - **绘图造型**：使用JSON格式 `"add_code_costume": {...}` (**不要**在python代码中写 `pygame.draw`)
   - **动态变化**：只有在运行时需要*实时改变*形状时，才在Python代码中绘制。
2. **使用库**：
   - 默认可用：`scrawl`, `pygame`
   - **必须导入**：`math`, `random`, `json`, `datetime` 等标准库必须显式 `import`。

## 代码编写原则
1. **必须定义 __init__**：务必定义 `__init__` 并第一行调用 `super().__init__()`。
2. **面向对象**：所有逻辑写在方法里，通过装饰器注册事件。

## 格式规范

### 1. 修改代码（Python）
```python:sprite:精灵名称
import random  # 显式导入

class 精灵类名(Sprite):
    def __init__(self):
        super().__init__()  # 必须调用！
        self.hp = 100  # 逻辑属性

    @as_main
    def main_loop(self):
        while True:
            self.move(5)
            yield 0
```

### 2. 修改属性/添加造型（JSON）
**注意：添加代码绘制造型属于IDE属性配置，必须用此JSON格式，而不是Python代码！**
```json:sprite:精灵名称
{
    "x": 100, 
    "y": 200,
    "add_code_costume": {
        "name": "造型名",
        "width": 40,
        "height": 30,
        "draw_code": "pygame.draw.circle(surface, (255,0,0), (20,15), 15)"
    }
}
```
**draw_code说明**：
- 坐标系：(0,0)为Surface左上角
- 多行：使用 `\\n` 分隔
- 变量：`surface`, `width`, `height` 可用

"""
        # Add Scrawl API documentation
        prompt += self._get_api_documentation()

        if context:
            prompt += f"\n当前项目上下文：\n{context}\n"

        prompt += "\n请用中文回答，严格遵守'严禁事项'和'正确工作流'。"
        return prompt

    def send_message(self, user_message: str, context: str = ""):
        """Send message to AI."""
        endpoint, api_key, model = self.get_current_config()
        if not api_key:
            self.error_occurred.emit("请先在设置中配置API Key或选择免费模型")
            return

        # Add user message
        self._messages.append(Message("user", user_message))

        # Build messages for API
        messages = [{"role": "system", "content": self.get_system_prompt(context)}]
        for msg in self._messages[-10:]:  # Keep last 10 messages
            messages.append({"role": msg.role, "content": msg.content})

        # Start worker
        self._worker = AIWorker(endpoint, api_key, model, messages)
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
        doc = """## Scrawl引擎API文档

### IDE与代码的职责划分
| 由IDE管理（初始值） | 由代码控制（运行时） |
|-----------|-----------|
| 精灵位置(x,y) | 移动、滑行等动态位置变化 |
| 精灵大小(size) | 动态缩放效果 |
| 精灵方向(direction) | 旋转、面向目标 |
| 可见性(visible) | 显示/隐藏逻辑 |
| 造型列表 | 造型切换、动画 |
| 物理属性初始值 | 运行时物理行为 |

### 坐标系与锚点（重要！）
- **屏幕坐标**：(0, 0) 为屏幕左上角。x向右增加，y向下增加。
- **精灵锚点**：精灵的 `(x, y)` 属性对应其**图片中心点**。
- **UI布局提示**：
    - 左上角对齐：`x = width/2`, `y = height/2`
    - 顶部居中：`x = SCREEN_WIDTH/2`, `y = height/2`
    - 右下角对齐：`x = SCREEN_WIDTH - width/2`, `y = SCREEN_HEIGHT - height/2`

### Sprite类核心属性
| 属性 | 类型 | 说明 |
|------|------|------|
| self.pos | pygame.Vector2 | 位置，用self.pos.x和self.pos.y |
| self.direction | float | 方向角度（0=右，90=上） |
| self.size | float | 缩放比例 |
| self.visible | bool | 是否可见 |
| self.name | str | 精灵名称 |

**重要：使用self.pos.x/self.pos.y，不是self.x/self.y**

### PhysicsSprite额外属性
| 属性 | 类型 | 说明 |
|------|------|------|
| self.velocity | pygame.Vector2 | 速度向量 |
| self.gravity | pygame.Vector2 | 重力向量 |
| self.friction | float | 摩擦力(0-1) |
| self.elasticity | float | 弹性系数 |

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
| yield from self.glide_left(dist, duration) | 向左滑行(ms) |
| yield from self.glide_right(dist, duration) | 向右滑行(ms) |
| yield from self.glide_up(dist, duration) | 向上滑行(ms) |
| yield from self.glide_down(dist, duration) | 向下滑行(ms) |

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
| yield from self.glide_to_mouse(duration) | 滑行到鼠标位置(ms) |

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
| self.add_costume(name, image) | 添加造型（image可以是pygame.Surface或图片路径） |
| self.switch_costume(name) | 切换到指定造型 |
| self.next_costume() | 切换到下一个造型 |
| self.set_image(image) | 设置默认图像 |

### 代码绘制造型（重要功能）
IDE支持使用pygame代码绘制造型，无需图片文件。在__init__中创建pygame.Surface并绘制：

```python
# 创建透明Surface
surface = pygame.Surface((宽度, 高度), pygame.SRCALPHA)

# 使用pygame绑制图形
pygame.draw.rect(surface, (R, G, B), (x, y, w, h))  # 矩形
pygame.draw.circle(surface, (R, G, B), (cx, cy), radius)  # 圆形
pygame.draw.ellipse(surface, (R, G, B), (x, y, w, h))  # 椭圆
pygame.draw.polygon(surface, (R, G, B), [(x1,y1), (x2,y2), ...])  # 多边形
pygame.draw.line(surface, (R, G, B), (x1, y1), (x2, y2), width)  # 线条

# 添加为造型
self.add_costume("造型名", surface)
```

**代码绘制造型示例（小鸟）：**
```python
bird_width, bird_height = 24, 17
surface = pygame.Surface((bird_width, bird_height), pygame.SRCALPHA)
pygame.draw.ellipse(surface, (255, 200, 0), (0, 0, bird_width, bird_height))  # 身体
pygame.draw.circle(surface, (255, 100, 0), (bird_width - 9, 6), 3)  # 头
pygame.draw.polygon(surface, (255, 0, 0), [(bird_width-6, 6), (bird_width+4, 6), (bird_width-1, 8)])  # 嘴
pygame.draw.ellipse(surface, (0, 0, 0), (bird_width - 12, 4, 3, 3))  # 眼睛
self.add_costume("default", surface)
```

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
| self.play_note(note, duration) | 播放音符(C4-C5，ms) |
| self.play_drum(type, duration) | 播放鼓声(ms) |
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
| self.say(text, duration) | 显示对话气泡(duration为毫秒，默认2000) |
| self.think(text, duration) | 显示思考气泡(duration为毫秒) |
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

@on_sprite_collision("TargetSpriteName")
def on_hit_other(self, other):
    \"\"\"碰到指定名称的精灵时触发（使用字符串）\"\"\"
    yield
```

"""

    def _get_code_examples(self) -> str:
        """Get code examples."""
        return """
### 完整交互示例 (Few-Shot Example)

**用户**：做一个接苹果的游戏。有个碗在下面左右移动，苹果从上面掉下来，接到加分。

**AI**：

**思考**：
1.  **需求分析**：需要三个精灵（碗、苹果、分数板）。
2.  **精灵配置**：
    *   `Bowl`：底部半圆（代码绘制）。
    *   `Apple`：顶部圆形（代码绘制）。
    *   `ScoreBoard`：显示分数（动态文字渲染）。
3.  **库检查**：`Apple`需 `random`；`ScoreBoard`需 `pygame.font`（包含在pygame中）。
4.  **安全检查**：循环中使用 `yield`。

---

#### 1. 配置碗 (Bowl) - JSON
```json:sprite:Bowl
{
    "x": 400,
    "y": 500,
    "add_code_costume": {
        "name": "bowl",
        "width": 60,
        "height": 30,
        "draw_code": "pygame.draw.arc(surface, (200, 150, 100), (0, 0, 60, 60), 3.14, 6.28, 5)\\npygame.draw.line(surface, (200, 150, 100), (0, 30), (60, 30), 5)"
    }
}
```

#### 2. 碗的逻辑 (Bowl) - Python
```python:sprite:Bowl
class Bowl(Sprite):
    def __init__(self):
        super().__init__()
        self.speed = 8

    @as_main
    def main_loop(self):
        while True:
            # 左右移动控制
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.pos.x -= self.speed
            if keys[pygame.K_RIGHT]:
                self.pos.x += self.speed
            
            # 限制在屏幕内
            if self.pos.x < 30: self.pos.x = 30
            if self.pos.x > 770: self.pos.x = 770
            
            yield 0
```

#### 3. 配置苹果 (Apple) - JSON
```json:sprite:Apple
{
    "x": 400,
    "y": -50,
    "add_code_costume": {
        "name": "red_apple",
        "width": 30,
        "height": 30,
        "draw_code": "pygame.draw.circle(surface, (255, 0, 0), (15, 15), 14)\\npygame.draw.line(surface, (0, 255, 0), (15, 0), (15, 5), 2)"
    }
}
```

#### 4. 苹果的逻辑 (Apple) - Python
```python:sprite:Apple
import random  # 必须显式导入！

class Apple(Sprite):
    def __init__(self):
        super().__init__()
        self.reset_position()

    @as_main
    def main_loop(self):
        self.reset_position()
        while True:
            self.pos.y += 5  # 下落
            
            # 掉出屏幕重置
            if self.pos.y > 600:
                self.reset_position()
                
            yield 0

    def reset_position(self):
        self.pos.y = -50
        self.pos.x = random.randint(50, 750)

    @on_sprite_collision("Bowl")
    def on_caught(self, bowl):
        self.broadcast("score_up")
        self.reset_position()
```

#### 5. 分数板配置 (ScoreBoard) - JSON
```json:sprite:ScoreBoard
{
    "x": 80,
    "y": 30,
    "add_code_costume": {
        "name": "default",
        "width": 100,
        "height": 30,
        "draw_code": "" 
    }
}
```

#### 6. 分数板逻辑 (ScoreBoard) - Python
```python:sprite:ScoreBoard
class ScoreBoard(Sprite):
    def __init__(self):
        super().__init__()
        self.score = 0
class ScoreBoard(Sprite):
    def __init__(self):
        super().__init__()
        self.score = 0
        self.update_display()

    def update_display(self):
        # 动态绘制：创建Surface -> 绘制文字 -> 设为造型
        if not self.game: return
        
        text = f"Score: {self.score}"
        # 使用 self.game.font 保证字体统一
        text_surf = self.game.font.render(text, True, (255, 255, 255))
        
        surface = pygame.Surface((150, 30), pygame.SRCALPHA)
        surface.blit(text_surf, (0, 0))
        self.add_costume("default", surface)

    @on_broadcast("score_up")
    def on_score(self):
        self.score += 1
        self.update_display()
```

### 克隆体示例 (Cloning Example)

**用户**：做一个下雪的效果。雪花随机出现在顶部，飘落到底部消失。

**AI**：

#### 1. 雪花配置 (Snowflake) - JSON
```json:sprite:Snowflake
{
    "x": -100, 
    "y": -100,
    "add_code_costume": {
        "name": "snow",
        "width": 10,
        "height": 10,
        "draw_code": "pygame.draw.circle(surface, (255, 255, 255), (5, 5), 4)"
    }
}
```

#### 2. 雪花逻辑 (Snowflake) - Python
```python:sprite:Snowflake
import random

class Snowflake(Sprite):
    def __init__(self):
        super().__init__()
        self.visible = False  # 本体隐藏，作为模板

    @as_main
    def spawner(self):
        \"\"\"生成器逻辑\"\"\"
        while True:
            self.clone()  # 克隆自己
            yield 100     # 每0.1秒生成一个

    @as_clones
    def fall_logic(self):
        \"\"\"克隆体逻辑\"\"\"
        # 1. 初始设置
        self.visible = True
        self.pos.x = random.randint(0, 800)
        self.pos.y = -10
        self.set_size(random.uniform(0.5, 1.5))
        
        # 2. 运动循环
        while self.pos.y < 610:
            self.pos.y += 3
            self.pos.x += random.uniform(-1, 1) # 微微摆动
            yield 0
            
        # 3. 销毁
        self.delete_self()
```
"""
