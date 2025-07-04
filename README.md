# Scrawl - A Scratch-like Python Game Engine

[中文](README_zh.md) | English

For Chinese documentation, click **中文**. Scrawl QQ 交流群: **1001578435**

<img src="https://github.com/user-attachments/assets/f3e9e30b-7132-47e6-abd5-c39332a920be" width="200" />

Scrawl is a Scratch-like game engine based on Pygame, designed to provide developers with an intuitive programming experience similar to Scratch, while leveraging Python's powerful capabilities.

## Best Demo

Witch Game: https://github.com/streetartist/scrawl_demo_witch

## Core Features

-   🧩 **Scratch-like Development Paradigm**: Use decorators to mark main coroutines, clone coroutines, and event handler coroutines
-   🎮 **Built-in Game Object System**: Ready-to-use sprites, scenes, particle systems, and more
-   ⚙️ **Physics Engine Integration**: Supports physical properties like velocity, gravity, elasticity, etc.
-   📻 **Broadcast Messaging System**: Component communication mechanism
-   🔧 **Debugging Tools**: Real-time display of FPS, sprite count, and other debug information
-   🎨 **Drawing Tools**: Supports pen drawing
-   🚀 **Coroutine Task System**: Coroutine mechanism supports intuitive `while True` loops

## Quick Start

The following code demonstrates the basic usage of Scrawl:

**Example 1:**

```python
from scrawl import *
import pygame

# svg files from https://scratch.mit.edu/projects/239626199/editor/

# Create game instance
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
            # Add bat
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

# Define scene
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        bat = Bat()
        self.add_sprite(bat)
        witch = Witch()
        self.add_sprite(witch)

# Run game
game.set_scene(MyScene())
game.run(fps=60)
```

*The video appears slow due to VNC recording. Runs quite smoothly when sprite count is below 200.*

https://github.com/user-attachments/assets/7398ac8f-689e-4088-9d78-414272c99438

**Example 2:**

```python
from scrawl import Game, Scene, Sprite, Cat, as_main

# Create game instance
game = Game()

class MyCat(Cat):
    def __init__(self):
        super().__init__()

    @as_main
    def main1(self):
        while True:
            self.walk()
            yield 500

# Define scene
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        # Add sprite
        cat = MyCat()
        self.add_sprite(cat)

# Run game
game.set_scene(MyScene())
game.run()
```

![Screen Capture 2025-06-15 090207](https://github.com/user-attachments/assets/2842db4a-147a-466e-ad69-4d74c24ba4b4)

**Example 3:**

```python
from scrawl import *
import time

# Create game instance
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

# Define scene
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        # Add sprite
        ball = Ball()
        self.add_sprite(ball)

    @as_main
    def main1(self):
        while True:
            # Add particle system
            explosion = ParticleSystem(400, 300)
            self.add_particles(explosion)  # Add particle system to scene
            self.broadcast("event")
            yield 3000

# Run game
game.set_scene(MyScene())
game.run()
```

https://github.com/user-attachments/assets/ef1a03d8-28b6-4bff-acf7-5f96be02f35a

## Core Concepts

### 1. Game Main Loop (`Game` Class)
-   Handles event loop
-   Manages scene switching
-   Controls frame rate and debug information

### 2. Scene (`Scene` Class)
-   Serves as game container
-   Manages sprites and particle systems
-   Handles global events and broadcast messages

### 3. Sprite (`Sprite` and `PhysicsSprite` Classes)
-   Basic game entities
-   Support properties like position, direction, size
-   Physics sprites support velocity, gravity, and other physical properties

#### Common Methods:
-   `move()`, `goto()`, `turn_left()`, `turn_right()`
-   `say()`, `clone()`, `delete_self()`
-   `apply_impulse()`, `set_gravity()` (for physics sprites)

### 4. Event System
-   **Broadcast Mechanism**: Component communication
-   **Key Binding**: Global and scene-level bindings
-   **Sprite Events**: Supports collision detection

## Documentation Index

1.  **Core Class Reference**
    -   Game - Game Controller
    -   Scene - Game Scene
    -   Sprite - Base Sprite Class
    -   PhysicsSprite - Physics Sprite Class
2.  **Decorator System**
    -   `@as_main` - Marks main behavior coroutine
    -   `@as_clones` - Marks clone behavior
    -   `@handle_broadcast` - Broadcast handler
3.  **Advanced Features**
    -   Particle Systems
    -   Drawing Tools
    -   Collision Detection
    -   Physics System

## Installation

```bash
pip install scrawl-engine
```

Upgrade

```bash
pip install --upgrade scrawl-engine
```

## Development Documentation (Tentative Version)

# Scrawl Library Usage Documentation

## Table of Contents

- Core Concepts
  - Game Class
  - Scene Class
  - Sprite Class
- Event Handling
  - Key Events
  - Collision Detection
  - Broadcast Events
- Sprite Cloning
  - Creating Clones
  - Clone Behavior
- Resource Management
  - Adding Images
  - Using Fonts
- Advanced Features
  - Physics Sprites
  - Particle Systems
  - Pen Effects
- Debugging Tools
  - Debug Mode
  - Performance Monitoring

---

## Core Concepts
### Game Class
Main game controller responsible for initialization and running game loop:
```python
game = Game(
    width=800, 
    height=600, 
    title="Game Title",
    font_path="font.ttf",
    font_size=20,
    fullscreen=False
)
game.set_scene(MyScene()) # Set scene
game.run(fps=60, debug=True)
```

### Scene Class
Game scene container for managing sprites and particle systems:
```python
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        # Add sprite
        self.add_sprite(MySprite())
    
    @as_main    
    def main1():
        pass # Scene main function
# Set scene
game.set_scene(MyScene())
```

### Sprite Class
Basic elements in the game with properties like position, direction, size:
```python
class MySprite(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "Sprite Name"
        self.pos = pygame.Vector2(100, 100)
        self.direction = 90  # 0=right, 90=up
        self.size = 1.0
        self.visible = True

    @as_main   
    def main1(self):
        while True:
            # Sprite main function
            self.move(5)
            yield 2000 # Delay 2000ms
```
---
## Event Handling
### Key Events
Handle key events using decorators:
```python
@on_key(pygame.K_SPACE, "pressed")  # Triggered on press
def space_pressed(self):
    print("Space pressed")
@on_key(pygame.K_LEFT, "held")  # Continuously triggered while held
def left_held(self):
    self.turn_left(2)
```

### Collision Detection
Handle collisions between sprites and with boundaries:
```python
# Edge collision detection
@handle_edge_collision("left")  # Collide with left edge
def hit_left(self):
    self.say("Hit left wall")
# Sprite collision detection
@handle_sprite_collision("Enemy")  # Collide with sprite named "Enemy"
def hit_enemy(self, other):
    self.delete_self()
```

### Broadcast Events
Communication mechanism between sprites and scenes:
```python
# Broadcast event
self.broadcast("gameover")
# Handle broadcast event
@handle_broadcast("gameover")
def on_gameover(self):
    self.visible = True
```
---
## Sprite Cloning
### Creating Clones
Clone existing sprites:
```python
# Clone self
self.clone()
# Clone other sprite
self.clone(other_sprite)
```

### Clone Behavior
Define logic specific to clones:
```python
class Bat(Sprite):
    @as_clones  # Mark as clone task
    def clones_behavior(self):
        self.visible = True
        while True:
            self.move(5)
            yield 200  # Move every 200ms
```
---
## Resource Management
### Adding Images
Add multiple costumes for sprites:
```python
self.add_costume("costume1", pygame.image.load("cat1.svg"))
self.add_costume("costume2", pygame.image.load("cat2.svg"))
self.switch_costume("costume1")  # Switch costume
self.next_costume()  # Switch to next costume
```

### Using Fonts
Game font settings:
```python
game = Game(
    font_path="Simhei.ttf",  # Supports Chinese fonts
    font_size=20
)
```
---
## Advanced Features
### Physics Sprites
Sprites with physical properties (velocity, gravity, friction):
```python
class PhysicsBall(PhysicsSprite):
    def __init__(self):
        super().__init__()
        self.velocity = pygame.Vector2(0, 5)
        self.gravity = pygame.Vector2(0, 0.2)
        self.elasticity = 0.8  # Elasticity coefficient
```

### Particle Systems
Create particle effects:
```python
# Create particle system at specified position
self.scene.add_particles(
    ParticleSystem(
        x=100, 
        y=100, 
        count=50,
        life_range=(500, 1500)
    )
)
```

### Pen Effects
Implement drawing functionality:
```python
# Enable pen
self.pen_down = True
self.pen_color = (255, 0, 0)
self.pen_size = 3
# Automatically record path when moving
self.move(100)
# Clear pen trails
self.clear_pen()
```
---
## Debugging Tools
### Debug Mode
Enable debug information display:
```python
game.run(debug=True)  # Enable debug mode
# Log debug information
game.log_debug("Sprite created")
```

### Performance Monitoring
Key performance metrics displayed on screen:
1. Real-time FPS
2. Number of sprites in scene
3. Current scene name
4. Custom debug information

## Contribution Guidelines

Welcome to submit issues and pull requests via GitHub:
https://github.com/streetartist/scrawl

---