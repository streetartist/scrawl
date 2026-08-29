# Scrawl - 类 Scratch 的 Python 游戏引擎

中文 | [English](README_en.md)

<p align="center">
  <img src="https://github.com/user-attachments/assets/f3e9e30b-7132-47e6-abd5-c39332a920be" width="200" alt="Scrawl logo" />
</p>

<p align="center">
  <a href="https://github.com/streetartist/scrawl">
    <img src="https://img.shields.io/badge/engine-Rust%20%2B%20Bevy-orange" alt="Rust and Bevy" />
  </a>
  <a href="https://pypi.org/project/scrawl-engine/">
    <img src="https://img.shields.io/pypi/v/scrawl-engine" alt="PyPI version" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-GPL--3.0-blue" alt="GPL-3.0 license" />
  </a>
  <a href="#社区">
    <img src="https://img.shields.io/badge/QQ%E7%BE%A4-1001578435-blue" alt="QQ群 1001578435" />
  </a>
</p>

Scrawl 是一个面向 Python 的 2D 游戏引擎，保留 Scratch 风格的精灵、场景、克隆、广播和事件编程体验，同时由 Rust 与 Bevy 负责窗口、渲染、输入、音频和 ECS 运行时。

从 2.2 开始，`scrawl` 就是唯一正式包和主线 API。旧 Pygame 后端及 `scrawl_v2` 入口均已移除。

## 核心特性

- 类 Scratch 编程模型：`Game`、`Scene`、`Sprite2D`、克隆和广播。
- 协程任务：生成器中 `yield` 的数字表示等待的毫秒数。
- 事件装饰器：键盘、鼠标、精灵点击、广播、边缘碰撞和精灵碰撞。
- Rust/Bevy 原生运行时：窗口、渲染、输入、音频及固定时间步主循环。
- 精灵渲染：纯色形状、PNG/SVG 造型、显隐、缩放、自定义宽高和 `z_index`。
- 游戏能力：文字与对话、画笔轨迹、音效、背景音乐和场景切换。
- Python 属性脏标记：静止精灵不会在每帧重复同步全部渲染属性。
- 统一场景树：启动时递归映射 `Scene`、`Node`、`Node2D` 和 `Sprite2D` 的父子层级。
- 运行时树同步：Node2D 的位置、旋转、缩放、层级和显隐变化，以及活动场景内 Node 的新增、删除、重挂载和克隆，均通过统一 bridge 队列同步到 ECS。
- 可视化 IDE：场景编辑、属性检查、代码编辑、运行与 AI 编程助手。

> `Node`、`Node2D`、`Sprite2D` 和基础物理节点已连接到 `NativeGame`；UI、TileMap、Particles 和 Navigation 仍在逐步接入。开始项目之前请查看[运行时能力表](docs/MANUAL.md#native-runtime-status)。

## 安装

Scrawl 需要 Python 3.8 或更高版本。

```bash
python -m pip install scrawl-engine
```

升级已安装版本：

```bash
python -m pip install --upgrade scrawl-engine
```

### 从源码开发

源码构建还需要 Rust stable：

```bash
git clone https://github.com/streetartist/scrawl.git
cd scrawl
python -m pip install -r requirements-dev.txt
python -m maturin develop --release
```

安装完成后可验证导入：

```bash
python -c "import scrawl; print(scrawl.__version__)"
```

## 快速开始

下面的示例创建两个精灵：小球自动移动并在边缘转向，玩家使用 WASD 移动。

```python
from scrawl import Game, Scene, Sprite2D, as_main, on_edge_collision, on_key


class Ball(Sprite2D):
    def __init__(self):
        super().__init__()
        self.name = "Ball"
        self.position = (400, 300)
        self.direction = 45
        self.color = (84, 193, 189)
        self.set_dimensions(48, 48)

    @as_main
    def move_forever(self):
        while True:
            self.move(3)
            yield 16

    @on_edge_collision("any")
    def bounce(self):
        self.turn_right(180)


class Player(Sprite2D):
    def __init__(self):
        super().__init__()
        self.name = "Player"
        self.position = (200, 200)
        self.color = (240, 106, 95)
        self.set_dimensions(56, 40)
        self.z_index = 1

    @on_key("w", "held")
    def up(self):
        self.move_up(5)

    @on_key("s", "held")
    def down(self):
        self.move_down(5)

    @on_key("a", "held")
    def left(self):
        self.move_left(5)

    @on_key("d", "held")
    def right(self):
        self.move_right(5)


class MainScene(Scene):
    def __init__(self):
        super().__init__("main")
        self.set_background_color(25, 32, 43)
        self.add_child(Ball())
        self.add_child(Player())


game = Game(width=800, height=600, title="My Scrawl Game")
game.set_scene(MainScene())
game.run(fps=60, debug=True)
```

坐标原点位于窗口左下角，X 向右、Y 向上。方向使用罗盘角度：`0` 向上，`90` 向右。

仓库提供了三个可运行示例：

```bash
python examples/basic_movement.py
python examples/node_hierarchy.py
python examples/witch.py
```

女巫示例包含造型动画、克隆、碰撞、广播和持久文字。素材来自 Scratch 项目，造型直接传入文件路径，不再经过 Pygame Surface。

Node hierarchy 示例覆盖启动时树映射，以及运行中的 Node2D 属性同步、子树新增、重挂载和删除。

## 核心概念

### Game

`Game` 创建原生窗口、保存场景并启动 Bevy 主循环。

```python
game = Game(
    width=1280,
    height=720,
    title="Game title",
    fps=60,
    fullscreen=False,
)
game.set_scene(MainScene())
game.run(debug=False, vsync=True)
```

可以通过 `add_scene()` 注册其他场景，再用场景名称切换：

```python
game.add_scene(PauseScene("pause"))
game.switch_scene("pause")
```

### Scene

`Scene` 是节点树根，管理子节点、背景和广播。添加节点时会自动建立 `node.scene` 与 `node.game` 引用。

```python
class MainScene(Scene):
    def __init__(self):
        super().__init__("main")
        self.set_background_color(30, 35, 45)
        self.set_background_image("assets/background.png")
        self.add_child(Player())
```

### Sprite2D

`Sprite2D` 是原生运行时当前最完整的可视节点。它继承 `Node2D`，同时保留 Scrawl 风格的易用属性和方法：

| 类别 | API |
| --- | --- |
| 变换 | `position`, `x`, `y`, `direction`, `size`, `move()`, `go_to()`, `point_towards()` |
| 外观 | `color`, `visible`, `width`, `height`, `z_index`, `set_dimensions()` |
| 造型 | `add_costume()`, `switch_costume()`, `next_costume()` |
| 生命周期 | `clone()`, `delete_self()` |
| 交互 | `say()`, `set_text()`, `broadcast()`, `play_sound()` |
| 画笔 | `pen_down()`, `pen_up()`, `set_pen_color()`, `set_pen_size()` |

造型必须传入文件系统路径：

```python
self.add_costume("idle", "assets/player-idle.svg")
self.add_costume("walk", "assets/player-walk.png")
self.switch_costume("walk")
```

## 事件与协程

事件处理器可以是普通函数，也可以是生成器。生成器每次 `yield` 一个毫秒数后由运行时继续调度。

```python
from scrawl import (
    as_clones,
    as_main,
    on_broadcast,
    on_edge_collision,
    on_key,
    on_mouse,
    on_sprite_clicked,
    on_sprite_collision,
)


@as_main
def main_task(self):
    while True:
        self.next_costume()
        yield 200


@as_clones
def clone_task(self):
    self.show()
    while True:
        self.move(5)
        yield 16


@on_key("space", "pressed")
def fire(self):
    self.clone(self.projectile)


@on_mouse(1, "pressed")
def mouse_down(self):
    self.say("clicked")


@on_sprite_clicked
def selected(self):
    self.color = (255, 200, 80)


@on_broadcast("game_over")
def game_over(self):
    self.set_text("Game Over", 36, (255, 255, 255))


@on_edge_collision("any")
def hit_edge(self):
    self.delete_self()


@on_sprite_collision("Enemy")
def hit_enemy(self):
    self.broadcast("lose_life")
```

按键使用字符串名称，例如 `"space"`、`"left"`、`"a"`。事件模式为 `"pressed"`、`"released"` 或 `"held"`。

## 克隆与广播

`clone()` 克隆当前精灵，`clone(other)` 在当前精灵的位置克隆另一个精灵。使用 `@as_clones` 定义克隆体启动后的行为。

```python
class Spawner(Sprite2D):
    def __init__(self):
        super().__init__()
        self.projectile = Projectile()

    @on_key("space", "pressed")
    def fire(self):
        self.projectile.direction = self.direction
        self.clone(self.projectile)
```

任意精灵或场景都可以发送广播：

```python
self.broadcast("score_changed")
```

所有带有 `@on_broadcast("score_changed")` 的处理器会收到该事件。

## 文字、画笔与音频

```python
self.say("Hello", duration=1500)
self.set_text("Score: 10", font_size=24, color=(255, 240, 120))

self.set_pen_color(255, 80, 80)
self.set_pen_size(3)
self.pen_down()
self.move(100)
self.pen_up()
```

音频先在 `Game` 注册，也可以直接传文件路径：

```python
game.load_sound("jump", "assets/jump.ogg")
game.load_music("bgm", "assets/background.ogg")
game.play_sound("jump")
game.play_music("bgm", loops=-1, volume=0.7)
game.pause_music()
game.unpause_music()
game.stop_music()
```

## 可视化 IDE

`scrawl_ide` 提供场景树、属性检查器、代码编辑器、运行器和 OpenAI 兼容的 AI 助手。IDE 仍在持续开发，建议同时保留项目版本控制。

```bash
python -m pip install -r scrawl_ide/requirements.txt
python scrawl_ide/main.py
```

AI 服务地址、模型和 API Key 在 IDE 设置中配置；凭据不会写入生成的游戏源码。

## 项目结构

```text
crates/
  scrawl-core/       ECS、场景和调度基础
  scrawl-render/     Bevy 渲染实现
  scrawl-input/      输入系统
  scrawl-audio/      音频系统
  scrawl-bridge/     PyO3 原生模块与 Python bridge
python/scrawl/       唯一正式 Python 包
examples/            当前 API 的可运行示例与素材
scrawl_ide/          可视化 IDE
docs/                手册、迁移说明、发布说明与路线图
tests/               Python API 测试
```

## 文档

- [运行时手册与能力表](docs/MANUAL.md)
- [从旧版迁移到 2.2](docs/MIGRATION_2.2.md)
- [2.2.0 发布说明](docs/RELEASE_NOTES_2.2.0.md)
- [路线图](docs/ROADMAP.md)

## 开发与验证

```bash
cargo check -p scrawl-bridge
cargo test -p scrawl-bridge
python -m unittest discover -s tests -v
```

提交前建议同时运行：

```bash
git diff --check
python examples/runtime_smoke.py
```

## 社区

- GitHub Issues / Pull Requests: https://github.com/streetartist/scrawl
- QQ 群：1001578435

Scrawl 使用 [GNU General Public License v3.0](LICENSE) 发布。
