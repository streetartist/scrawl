# Scrawl - A Scratch-like Python Game Engine

[中文](README.md) | English

<p align="center">
  <img src="https://github.com/user-attachments/assets/f3e9e30b-7132-47e6-abd5-c39332a920be" width="200" alt="Scrawl logo" />
</p>

<p align="center">
  <a href="https://github.com/streetartist/scrawl"><img src="https://img.shields.io/badge/engine-Rust%20%2B%20Bevy-orange" alt="Rust and Bevy" /></a>
  <a href="https://pypi.org/project/scrawl-engine/"><img src="https://img.shields.io/pypi/v/scrawl-engine" alt="PyPI version" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue" alt="GPL-3.0 license" /></a>
</p>

Scrawl is a Python-facing 2D game engine. It keeps the Scratch-style model of sprites, scenes, clones, broadcasts, and events while Rust and Bevy own the window, rendering, input, audio, and ECS runtime.

Starting with 2.2, `scrawl` is the only supported package and mainline API. The old Pygame backend and the `scrawl_v2` import path have been removed.

## Features

- Scratch-like `Game`, `Scene`, and `Sprite` model with clones and broadcasts.
- Coroutine tasks where a yielded number is a delay in milliseconds.
- Decorators for keyboard, mouse, sprite clicks, broadcasts, and collisions.
- Native Rust/Bevy window, renderer, input, audio, and fixed-step runtime.
- Shape and PNG/SVG sprites with visibility, scale, explicit dimensions, and `z_index`.
- Persistent text, speech, pen trails, sound effects, music, and scene switching.
- Dirty property synchronization so idle sprites do not resend every render property each frame.
- A unified startup scene tree for `Scene`, `Node`, `Node2D`, and `Sprite` hierarchy mapping.
- Runtime tree sync for Node2D transform, layer, and visibility changes plus node add, remove, same-scene reparent, and clone operations through one bridge queue.
- A visual IDE with scene editing, an inspector, code editing, running, and an AI assistant.

> The generic Node, UI, physics node, TileMap, Particles, and Navigation models are importable, but some are not connected to `NativeGame` yet. Check the [runtime capability table](docs/MANUAL.md#native-runtime-status) before depending on them.

## Installation

Scrawl requires Python 3.8 or newer.

```bash
python -m pip install scrawl-engine
```

Upgrade an existing installation:

```bash
python -m pip install --upgrade scrawl-engine
```

Building from source also requires stable Rust:

```bash
git clone https://github.com/streetartist/scrawl.git
cd scrawl
python -m pip install -r requirements-dev.txt
python -m maturin develop --release
python -c "import scrawl; print(scrawl.__version__)"
```

## Quick Start

```python
from scrawl import Game, Scene, Sprite, as_main, on_edge_collision, on_key


class Ball(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Ball"
        self.pos = (400, 300)
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


class Player(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Player"
        self.pos = (200, 200)
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
        self.add_sprite(Ball())
        self.add_sprite(Player())


game = Game(width=800, height=600, title="My Scrawl Game")
game.set_scene(MainScene())
game.run(fps=60, debug=True)
```

The coordinate origin is at the bottom left. X increases to the right and Y increases upward. Directions use compass degrees: `0` points up and `90` points right.

Run the repository examples with:

```bash
python examples/basic_movement.py
python examples/node_hierarchy.py
python examples/witch.py
```

The witch example demonstrates costume animation, clones, collisions, broadcasts, and persistent text. Costumes are filesystem paths; Pygame Surface objects are no longer supported.

The node hierarchy example covers startup hierarchy mapping plus runtime Node2D property sync, subtree creation, reparenting, and removal.

## Core Concepts

### Game and Scene

`Game` creates the native window, stores scenes, and starts the Bevy loop. `Scene` manages sprites, its background, and broadcasts.

```python
game = Game(width=1280, height=720, title="Game title", fps=60)
game.set_scene(MainScene("main"))
game.add_scene(PauseScene("pause"))
game.run(debug=False, vsync=True)
```

### Sprite

`Sprite` is currently the most complete game object in the native runtime.

| Area | API |
| --- | --- |
| Transform | `x`, `y`, `pos`, `direction`, `size`, `move()`, `go_to()`, `point_towards()` |
| Appearance | `color`, `visible`, `width`, `height`, `z_index`, `set_dimensions()` |
| Costumes | `add_costume()`, `switch_costume()`, `next_costume()` |
| Lifecycle | `clone()`, `delete_self()` |
| Interaction | `say()`, `set_text()`, `broadcast()`, `play_sound()` |
| Pen | `pen_down()`, `pen_up()`, `set_pen_color()`, `set_pen_size()` |

Costumes must be filesystem paths:

```python
self.add_costume("idle", "assets/player-idle.svg")
self.add_costume("walk", "assets/player-walk.png")
self.switch_costume("walk")
```

## Events and Coroutines

Handlers may be regular functions or generators. The runtime resumes a generator after the number of milliseconds it yields.

```python
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

Keys use string identifiers such as `"space"`, `"left"`, and `"a"`. Event modes are `"pressed"`, `"released"`, or `"held"`.

## Text, Pen, and Audio

```python
self.say("Hello", duration=1500)
self.set_text("Score: 10", font_size=24, color=(255, 240, 120))
self.set_pen_color(255, 80, 80)
self.set_pen_size(3)
self.pen_down()
self.move(100)
self.pen_up()

game.load_sound("jump", "assets/jump.ogg")
game.load_music("bgm", "assets/background.ogg")
game.play_sound("jump")
game.play_music("bgm", loops=-1, volume=0.7)
game.stop_music()
```

## Visual IDE

`scrawl_ide` provides a scene tree, inspector, code editor, runner, and an OpenAI-compatible AI assistant. It is still under active development, so keep generated projects under version control.

```bash
python -m pip install -r scrawl_ide/requirements.txt
python scrawl_ide/main.py
```

Configure the AI endpoint, model, and API key in the IDE settings. Credentials are not written into generated game source files.

## Repository Layout

```text
crates/              Rust engine crates and PyO3 bridge
python/scrawl/       The only supported Python package
examples/            Runnable examples and assets for the current API
scrawl_ide/          Visual IDE
docs/                Manual, migration guide, release notes, and roadmap
tests/               Python API tests
```

## Documentation

- [Runtime manual and capability table](docs/MANUAL.md)
- [Migrating older projects to 2.2](docs/MIGRATION_2.2.md)
- [2.2.0 release notes](docs/RELEASE_NOTES_2.2.0.md)
- [Roadmap](docs/ROADMAP.md)

## Development and Verification

```bash
cargo check -p scrawl-bridge
cargo test -p scrawl-bridge
python -m unittest discover -s tests -v
git diff --check
```

GitHub issues and pull requests are welcome at https://github.com/streetartist/scrawl. The QQ group is `1001578435`.

Scrawl is released under the [GNU General Public License v3.0](LICENSE).
