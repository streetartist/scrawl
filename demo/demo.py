from scrawl import *

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
game.run(debug=True)
