from scrawl import TkGUI
from scrawl import Game, Scene, Sprite, Cat, as_main, on_mouse_event
import tkinter as tk

class Gui(TkGUI):
    def main(self, root):
        # 使用标准的tkinter方式创建UI
        self.root = root
        
        # 创建主标题
        self.title_label = tk.Label(root, text="账 号 登 录", font=("Arial", 48))
        self.title_label.place(x=640, y=200, anchor="center")
        
        # 创建账号标签和输入框
        self.username_label = tk.Label(root, text="账号", font=("Arial", 12))
        self.username_label.place(x=450, y=300, anchor="nw")
        
        self.username_entry = tk.Entry(root, font=("Arial", 12), width=30)
        self.username_entry.place(x=450, y=340, width=380, height=50)
        self.username_entry.insert(0, "点击输入账号")
        self.username_entry.config(fg="gray")
        
        # 创建密码标签和输入框
        self.password_label = tk.Label(root, text="密码", font=("Arial", 12))
        self.password_label.place(x=450, y=400, anchor="nw")
        
        self.password_entry = tk.Entry(root, font=("Arial", 12), show="●", width=30)
        self.password_entry.place(x=450, y=440, width=380, height=50)
        self.password_entry.insert(0, "点击输入密码")
        self.password_entry.config(fg="gray")
        
        # 创建按钮
        self.register_button = tk.Button(root, text="注 册", font=("Arial", 12), 
                                       bg="#64ff64", fg="black",
                                       command=self.on_register)
        self.register_button.place(x=450, y=540, width=180, height=50)
        
        self.login_button = tk.Button(root, text="登 录", font=("Arial", 12), 
                                    bg="#64ff64", fg="black",
                                    command=self.on_login)
        self.login_button.place(x=650, y=540, width=180, height=50)
        
        # 绑定焦点事件
        self.username_entry.bind("<FocusIn>", lambda e: self.on_entry_focus_in(self.username_entry, "点击输入账号"))
        self.username_entry.bind("<FocusOut>", lambda e: self.on_entry_focus_out(self.username_entry, "点击输入账号"))
        self.password_entry.bind("<FocusIn>", lambda e: self.on_entry_focus_in(self.password_entry, "点击输入密码"))
        self.password_entry.bind("<FocusOut>", lambda e: self.on_entry_focus_out(self.password_entry, "点击输入密码"))
    
    def on_entry_focus_in(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg="black")
    
    def on_entry_focus_out(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg="gray")
    
    def on_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        print(f"注册 - 用户名: {username}, 密码: {password}")
    
    def on_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        print(f"登录 - 用户名: {username}, 密码: {password}")

gui = Gui("登录页面")

# 创建游戏实例
game = Game(fullscreen=True)

class MyCat(Cat):
    def __init__(self):
        super().__init__()

    @as_main
    def main1(self):
        while True:
            self.walk()
            yield 500

    @as_main
    def on_click(self):
        while True:
            if self.is_sprite_clicked(self.name):
                print(f"精灵 {self.name} 被点击了！")
                # 这里可以添加点击后的逻辑
                self.say("我被点击了！", 1000)  # 显示文字气泡
                gui.start()
            yield 0

# 定义场景
class MyScene(Scene):

    def __init__(self):
        super().__init__()

        # 添加精灵
        cat = MyCat()
        self.add_sprite(cat)

# 运行游戏
game.set_scene(MyScene())
game.run(debug=True)