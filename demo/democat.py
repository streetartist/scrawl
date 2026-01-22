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
