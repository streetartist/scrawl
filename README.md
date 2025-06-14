# Scrawl - Scratch-Like Python Game Engine

Scrawl 是一个基于 Pygame 的类 Scratch 游戏引擎，旨在为开发者提供类似 Scratch 的直觉式编程体验，同时保留 Python 的功能优势。

## 主要特性

- 🧩 **类似 Scratch 的开发范式**：使用装饰器标记主协程，克隆体协程，事件处理协程
- 🎮 **内置游戏对象系统**：精灵、场景、粒子系统等开箱即用
- ⚙️ **物理引擎集成**：支持速度、重力、弹性等物理特性
- 📻 **广播消息系统**：组件间通信机制
- 🔧 **调试工具**：实时显示 FPS、精灵数量等调试信息
- 🎨 **绘图工具**：支持画笔轨迹绘制
- 🚀 **协程任务系统**：使用协程机制，使符合直觉的while True成为可能

## 快速开始

以下代码展示了 Scrawl 的基本使用：

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

    def main(self):
        while True:
            # 添加粒子系统
            explosion = ParticleSystem(400, 300)
            self.add_particles(explosion)  # 添加粒子系统到场景
            self.broadcast("event")
            yield 3000


# 运行游戏
game.set_scene(MyScene())
game.run()
```

https://github.com/user-attachments/assets/ef1a03d8-28b6-4bff-acf7-5f96be02f35a

## 核心概念

### 1. 游戏主循环 (`Game` 类)
- 处理事件循环
- 管理场景切换
- 控制帧率与调试信息

### 2. 场景 (`Scene` 类)
- 作为游戏容器
- 管理精灵和粒子系统
- 处理全局事件和广播消息

#### 关键技术：
```python
@handle_broadcast("event_name")
@as_main
self.broadcast("event_name")
self.add_task(coroutine_function())
```

### 3. 精灵 (`Sprite` 和 `PhysicsSprite` 类)
- 基础游戏实体
- 支持位置、方向、大小等属性
- 物理精灵支持速度、重力等物理特性

#### 常用方法：
- `move()`,`goto()`,`turn_left()`,`turn_right()`
- `say()`,`clone()`,`delete_self()`
- `apply_impulse()`,`set_gravity()`(物理精灵专用)

### 4. 事件系统
- **广播机制**：组件间通信
- **按键绑定**：全局和场景级别绑定
- **精灵事件**：碰撞检测支持

## 文档目录

1. **核心类参考**
   - Game - 游戏控制器
   - Scene - 游戏场景
   - Sprite - 基础精灵类
   - PhysicsSprite - 物理精灵类

2. **装饰器系统**
   - `@as_main` - 标记主行为协程
   - `@as_clones` - 标记克隆体行为
   - `@handle_broadcast` - 广播处理器

3. **进阶功能**
   - 粒子系统
   - 画笔工具
   - 碰撞检测
   - 物理系统

## 安装

```bash
pip install scrawl-engine
```

## 开发文档

还没有完成……

## 贡献指南

欢迎通过 GitHub 提交问题和拉取请求：
https://github.com/streetartist/scrawl
