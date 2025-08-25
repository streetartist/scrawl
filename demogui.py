from scrawl import Game, Scene, Sprite, as_main

game = Game()

class GUISprite(Sprite):
    def __init__(self):
        super().__init__()

        self.title = "GUI演示"
        self.visible = False
    
    @as_main
    def main1(self):
        # 创建输入框
        self.gui.create_input('name_input', (100, 100, 200, 40), "请输入你的名字")
        # 创建按钮
        self.gui.create_button('submit_btn', 100,160, "提交",
                             callback=self.on_submit)
        # 创建结果显示标签
        self.gui.create_label('result_label', (100, 220, 300, 40), "点击提交按钮显示结果")

    def on_submit(self):
        name = self.gui.get_input_text('name_input')
        print(f"你好，{name}！")
        self.gui.set_label_text('result_label', f"你好，{name}！")

class GUIScene(Scene):
    def __init__(self):
        super().__init__()
        self.guisprite = GUISprite()
        self.add_sprite(self.guisprite)

if __name__ == "__main__":
    scene = GUIScene()
    game.set_scene(scene)
    game.run()