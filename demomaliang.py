from scrawl import TkGUI
from scrawl import Game, Scene, Sprite, Cat, as_main, on_mouse_event
import maliang

class Gui(TkGUI):
    def main(self, cv):
        # 使用maliang方式创建UI 
        maliang.Text(cv, (640, 200), text="账 号 登 录", fontsize=48, anchor="center")

        maliang.Text(cv, (450, 300), text="账号", anchor="nw")
        maliang.InputBox(cv, (450, 340), (380, 50), placeholder="点击输入账号")
        maliang.Text(cv, (450, 400), text="密码", anchor="nw")
        maliang.InputBox(cv, (450, 440), (380, 50), show="●", placeholder="点击输入密码")

        maliang.Button(cv, (450, 540), (180, 50), text="注 册")
        maliang.Button(cv, (650, 540), (180, 50), text="登 录")
        
gui = Gui("登录页面")

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

    @on_mouse_event(mode="pressed", button=1)  # 左键点击
    def on_click(self):
        print(f"精灵 {self.name} 被点击了！")
        # 这里可以添加点击后的逻辑
        self.say("我被点击了！", 1000)  # 显示文字气泡
        gui.start()

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