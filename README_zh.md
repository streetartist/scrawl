
# Scrawl - 类 Scratch 的 Python 游戏引擎

[中文](README_zh.md) | English

中文文档请点击 **中文**，Scrawl 交流QQ群：**1001578435**

<img src="https://github.com/user-attachments/assets/f3e9e30b-7132-47e6-abd5-c39332a920be" width="200" />

Scrawl 是一个基于 Pygame 的类 Scratch 游戏引擎，旨在为开发者提供类似 Scratch 的直观编程体验，同时借力 Python 的强大功能。

## 最佳 Demo

女巫游戏：https://github.com/streetartist/scrawl_demo_witch

## 核心特性

-   🧩 **类 Scratch 的开发范式**：使用装饰器标记主协程、克隆协程和事件处理协程
-   🎮 **内置游戏对象系统**：开箱即用的精灵（Sprite）、场景（Scene）、粒子系统等
-   ⚙️ **物理引擎集成**：支持速度、重力、弹性等物理属性
-   📻 **广播消息系统**：组件间通信机制
-   🔧 **调试工具**：实时显示 FPS、精灵数量等调试信息
-   🎨 **绘图工具**：支持画笔绘制
-   🚀 **协程任务系统**：协程机制支持直观的 `while True` 循环

## 快速入门

以下代码演示了 Scrawl 的基本用法：

**示例 1：**

```python
from scrawl import *
import pygame

# svg 文件来自 https://scratch.mit.edu/projects/239626199/editor/

# 创建游戏实例
game = Game()

class Bat(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Bat"
        self.add_costume("costume1", pygame.image.load("bat2-b.svg").convert_alpha())
        self.add_costume("costume2", pygame.image.load("bat2-a.svg").convert_alpha())
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
        self.delete_self()

    @handle_sprite_collision("FireBall")
    def hit_fireball(self, other):
        self.delete_self()

    @handle_sprite_collision("Witch")
    def hit_witch(self, other):
        self.delete_self()

class FireBall(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "FireBall"
        self.add_costume("costume1", pygame.image.load("ball-a.svg").convert_alpha())
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

class Witch(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Witch"
        self.add_costume("costume1", pygame.image.load("witch.svg").convert_alpha())
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
```

*视频看起来有点慢是因为通过 VNC 录制。当精灵数量少于 200 时，运行相当流畅。*

https://github.com/user-attachments/assets/7398ac8f-689e-4088-9d78-414272c99438

**示例 2：**

```python
from scrawl import Game, Scene, Sprite, Cat, as_main

# 创建游戏实例
game = Game()

class MyCat(Cat):
    def __init__(self):
        super().__init__()

    @as_main
    def main1(self):
        while True:
            self.walk()
            yield 500

# 定义场景
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        # 添加精灵
        cat = MyCat()
        self.add_sprite(cat)

# 运行游戏
game.set_scene(MyScene())
game.run()
```

![Screen Capture 2025-06-15 090207](https://github.com/user-attachments/assets/2842db4a-147a-466e-ad69-4d74c24ba4b4)

**示例 3：**

```python
from scrawl import *
import time

# 创建游戏实例
game = Game()

class Ball(Sprite):
    def __init__(self):
        super().__init__()

    @as_main
    def main1(self):
        while True:
            self.turn_left(10)
            self.move(10)
            yield 100
            self.clone()

    @as_clones
    def clones1(self):
        while True:
            self.turn_right(10)
            self.move(100)
            self.change_color_random()
            yield 1000

    @handle_broadcast("event")
    def event1(self):
        self.say("hello")

# 定义场景
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        # 添加精灵
        ball = Ball()
        self.add_sprite(ball)

    @as_main
    def main1(self):
        while True:
            # 添加粒子系统
            explosion = ParticleSystem(400, 300)
            self.add_particles(explosion)  # 将粒子系统添加到场景
            self.broadcast("event")
            yield 3000

# 运行游戏
game.set_scene(MyScene())
game.run()
```

https://github.com/user-attachments/assets/ef1a03d8-28b6-4bff-acf7-5f96be02f35a

## 核心概念

### 1. 游戏主循环 (`Game` 类)
-   处理事件循环
-   管理场景切换
-   控制帧率和调试信息

### 2. 场景 (`Scene` 类)
-   作为游戏容器
-   管理精灵和粒子系统
-   处理全局事件和广播消息

### 3. 精灵 (`Sprite` 和 `PhysicsSprite` 类)
-   基本的游戏实体
-   支持位置、方向、大小等属性
-   物理精灵支持速度、重力等物理特性

#### 常用方法:
-   `move()`, `goto()`, `turn_left()`, `turn_right()`
-   `say()`, `clone()`, `delete_self()`
-   `apply_impulse()`, `set_gravity()` (用于物理精灵)

### 4. 事件系统
-   **广播机制**：组件间通信
-   **按键绑定**：全局和场景级别的绑定
-   **精灵事件**：支持碰撞检测

## 文档索引

1.  **核心类参考**
    -   Game - 游戏控制器
    -   Scene - 游戏场景
    -   Sprite - 基础精灵类
    -   PhysicsSprite - 物理精灵类
2.  **装饰器系统**
    -   `@as_main` - 标记主行为协程
    -   `@as_clones` - 标记克隆行为
    -   `@handle_broadcast` - 广播处理程序
3.  **高级特性**
    -   粒子系统
    -   绘图工具
    -   碰撞检测
    -   物理系统

## 安装

```bash
pip install scrawl-engine
```

## 开发文档

即将推出...

## 贡献指南

欢迎通过 GitHub 提交 issues 和 pull requests：
https://github.com/streetartist/scrawl

---