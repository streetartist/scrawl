# Scrawl - Scratch-Like Python Game Engine

[中文](README_zh.md) | English

<img src="https://github.com/user-attachments/assets/f3e9e30b-7132-47e6-abd5-c39332a920be" width="200" />

Scrawl is a Scratch-like game engine based on Pygame, designed to provide developers with an intuitive programming experience similar to Scratch, while retaining the power of Python.

## Key Features

- 🧩 **Scratch-like Development Paradigm**: Use decorators to mark main coroutines, clone coroutines, and event handler coroutines
- 🎮 **Built-in Game Object System**: Ready-to-use sprites, scenes, particle systems, and more
- ⚙️ **Physics Engine Integration**: Support for velocity, gravity, elasticity, and other physical properties
- 📻 **Broadcast Message System**: Component communication mechanism
- 🔧 **Debugging Tools**: Real-time display of FPS, sprite count and other debug information
- 🎨 **Drawing Tools**: Support for pen stroke drawing
- 🚀 **Coroutine Task System**: Coroutine mechanism enables intuitive while True loops

## Quick Start

The following code demonstrates basic usage of Scrawl:

Example 1:

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

Example 2

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

    def main(self):
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

### 1. Game Main Loop (`Game` class)
- Handles event loop
- Manages scene switching
- Controls frame rate and debug information

### 2. Scene (`Scene` class)
- Serves as game container
- Manages sprites and particle systems
- Handles global events and broadcast messages

### 3. Sprites (`Sprite` and `PhysicsSprite` classes)
- Basic game entities
- Support position, direction, size and other properties
- Physics sprites support velocity, gravity and other physical characteristics

#### Common Methods:
- `move()`, `goto()`, `turn_left()`, `turn_right()`
- `say()`, `clone()`, `delete_self()`
- `apply_impulse()`, `set_gravity()` (for physics sprites)

### 4. Event System
- **Broadcast Mechanism**: Component communication
- **Key Binding**: Global and scene-level binding
- **Sprite Events**: Collision detection support

## Documentation Index

1. **Core Class Reference**
   - Game - Game controller
   - Scene - Game scene
   - Sprite - Basic sprite class
   - PhysicsSprite - Physics sprite class

2. **Decorator System**
   - `@as_main` - Mark main behavior coroutine
   - `@as_clones` - Mark clone behavior
   - `@handle_broadcast` - Broadcast handler

3. **Advanced Features**
   - Particle System
   - Drawing Tools
   - Collision Detection
   - Physics System

## Installation

```bash
pip install scrawl-engine
```

## Development Documentation

Coming soon...

## Contribution Guide

Welcome to submit issues and pull requests via GitHub:
https://github.com/streetartist/scrawl
