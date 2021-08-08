# scrawl
A game engine like Scratch which can run on Node.js Pygame &amp; Kivy

## 介绍
Scrawl是一个游戏引擎，允许您使用Scratch的方式编写游戏。（克隆 事件）

它支持Pgzero Arcade Wasabi2d 和 Node.js，这让它能运行在绝大多数平台。

它包含大部分所有可能使用的功能（Api 文件读写 等）

它支持开发者开发扩展包

完全不用担心“While True”的问题，只需要自然的编程就可以

搭配强大的游戏IDE Mint Editor,极大简化游戏编写

## 示例
```python
from scrawl import Scene, Sprite, Game

class Cat(Sprite):
    def __init__(self):
        self.image = "cat.png"
    
    def main(self):
        while True:
            self.move(10)
            yield 1000
            self.clone()
    
    def event(self):
        self.say("hello")

    def clones(self):
        self.turn_right(10)

class Background(Scene):
    def __init__(self):
        self.image = "bg.png"

    def main(self):
        while True:
            yield 500
            self.broadcast("event")

class Main(Game):
    def __init__(self):
        self.scene = Background()
        self.sprite = [
            Cat(),
        ]

Main().run(engine="pygame")
```
