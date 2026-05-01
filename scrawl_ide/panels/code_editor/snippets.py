"""
Code Snippets for Scrawl IDE

Defines decorator and function templates for quick insertion.
Uses scrawl_v2 API.
"""

from typing import List, Dict, Any


# Decorator snippets
DECORATOR_SNIPPETS: List[Dict[str, Any]] = [
    {
        "name": "@on_key",
        "category": "事件",
        "description": "键盘按键事件",
        "template": '''@on_key("space", "pressed")
    def on_key_space(self):
        """按下空格键时触发"""
        pass
''',
    },
    {
        "name": "@on_mouse",
        "category": "事件",
        "description": "鼠标事件",
        "template": '''@on_mouse("click")
    def on_mouse_click(self):
        """鼠标点击时触发"""
        pass
''',
    },
    {
        "name": "@on_sprite_clicked",
        "category": "事件",
        "description": "精灵被点击事件",
        "template": '''@on_sprite_clicked
    def on_clicked(self):
        """精灵被点击时触发"""
        pass
''',
    },
    {
        "name": "@on_sprite_collision",
        "category": "事件",
        "description": "精灵碰撞事件",
        "template": '''@on_sprite_collision("OtherSprite")
    def on_collision(self, other):
        """与指定精灵碰撞时触发"""
        pass
''',
    },
    {
        "name": "@on_edge_collision",
        "category": "事件",
        "description": "边缘碰撞事件",
        "template": '''@on_edge_collision
    def on_edge_hit(self, edge):
        """碰到边缘时触发，edge为 'left'/'right'/'top'/'bottom'"""
        pass
''',
    },
    {
        "name": "@on_broadcast",
        "category": "事件",
        "description": "广播消息事件",
        "template": '''@on_broadcast("message_name")
    def on_message(self):
        """收到广播消息时触发"""
        pass
''',
    },
    {
        "name": "@as_main",
        "category": "循环",
        "description": "主循环（生成器）",
        "template": '''@as_main
    def main_loop(self):
        """主循环"""
        while True:
            # 在这里添加逻辑
            yield 0
''',
    },
    {
        "name": "@as_clones",
        "category": "循环",
        "description": "克隆体循环（生成器）",
        "template": '''@as_clones
    def clone_loop(self):
        """克隆体循环"""
        while True:
            # 克隆体逻辑
            yield 0
''',
    },
]


# Function snippets - organized by category
FUNCTION_SNIPPETS: List[Dict[str, Any]] = [
    # Movement
    {
        "name": "go_to(x, y)",
        "category": "移动",
        "description": "移动到指定位置",
        "template": "self.go_to(x, y)",
    },
    {
        "name": "move(steps)",
        "category": "移动",
        "description": "向当前方向移动",
        "template": "self.move(10)",
    },
    {
        "name": "glide_to(x, y, duration)",
        "category": "移动",
        "description": "滑动到指定位置",
        "template": "yield from self.glide_to(x, y, duration=1.0)",
    },
    {
        "name": "point_towards(target)",
        "category": "移动",
        "description": "面向目标",
        "template": "self.point_towards(target)",
    },
    {
        "name": "turn_left(degrees)",
        "category": "移动",
        "description": "左转",
        "template": "self.turn_left(15)",
    },
    {
        "name": "turn_right(degrees)",
        "category": "移动",
        "description": "右转",
        "template": "self.turn_right(15)",
    },
    {
        "name": "bounce_on_edge()",
        "category": "移动",
        "description": "碰到边缘反弹",
        "template": "self.bounce_on_edge()",
    },
    # Appearance
    {
        "name": "say(text, duration)",
        "category": "外观",
        "description": "说话气泡",
        "template": 'self.say("Hello!", duration=2)',
    },
    {
        "name": "think(text, duration)",
        "category": "外观",
        "description": "思考气泡",
        "template": 'self.think("Hmm...", duration=2)',
    },
    {
        "name": "switch_costume(name)",
        "category": "外观",
        "description": "切换造型",
        "template": 'self.switch_costume("costume_name")',
    },
    {
        "name": "next_costume()",
        "category": "外观",
        "description": "下一个造型",
        "template": "self.next_costume()",
    },
    {
        "name": "set_size(scale)",
        "category": "外观",
        "description": "设置大小",
        "template": "self.set_size(1.0)",
    },
    {
        "name": "show()",
        "category": "外观",
        "description": "显示",
        "template": "self.show()",
    },
    {
        "name": "hide()",
        "category": "外观",
        "description": "隐藏",
        "template": "self.hide()",
    },
    # Detection
    {
        "name": "is_touching(target)",
        "category": "侦测",
        "description": "是否碰到精灵",
        "template": 'if self.is_touching("SpriteName"):',
    },
    {
        "name": "is_touching_edge()",
        "category": "侦测",
        "description": "是否碰到边缘",
        "template": "if self.is_touching_edge():",
    },
    {
        "name": "is_key_pressed(key)",
        "category": "侦测",
        "description": "按键是否按下",
        "template": 'if self.is_key_pressed("space"):',
    },
    {
        "name": "Input.is_action_pressed",
        "category": "侦测",
        "description": "输入映射动作检测",
        "template": 'if Input.is_action_pressed("move_right"):',
    },
    {
        "name": "Input.get_vector",
        "category": "侦测",
        "description": "获取方向向量（WASD/箭头）",
        "template": 'direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")',
    },
    {
        "name": "is_mouse_down()",
        "category": "侦测",
        "description": "鼠标是否按下",
        "template": "if self.is_mouse_down():",
    },
    {
        "name": "distance_to(target)",
        "category": "侦测",
        "description": "到目标的距离",
        "template": 'dist = self.distance_to("SpriteName")',
    },
    # Control
    {
        "name": "clone()",
        "category": "控制",
        "description": "创建克隆体",
        "template": "self.clone()",
    },
    {
        "name": "delete_clone()",
        "category": "控制",
        "description": "删除克隆体",
        "template": "self.delete_clone()",
    },
    {
        "name": "broadcast(message)",
        "category": "控制",
        "description": "广播消息",
        "template": 'self.broadcast("message_name")',
    },
    {
        "name": "wait(seconds)",
        "category": "控制",
        "description": "等待（在生成器中使用）",
        "template": "yield from self.wait(1.0)",
    },
    # Physics (PhysicsSprite)
    {
        "name": "set_gravity(x, y)",
        "category": "物理",
        "description": "设置重力",
        "template": "self.set_gravity(0, 0.5)",
    },
    {
        "name": "set_friction(value)",
        "category": "物理",
        "description": "设置摩擦力",
        "template": "self.set_friction(0.1)",
    },
    {
        "name": "set_elasticity(value)",
        "category": "物理",
        "description": "设置弹性",
        "template": "self.set_elasticity(0.8)",
    },
    {
        "name": "apply_force(fx, fy)",
        "category": "物理",
        "description": "施加力",
        "template": "self.apply_force(0, -10)",
    },
    # Scrawl V2 - Audio
    {
        "name": "AudioManager.load",
        "category": "音频",
        "description": "加载音效",
        "template": 'AudioManager.load("effect_name", "sounds/effect.ogg")',
    },
    {
        "name": "AudioManager.play",
        "category": "音频",
        "description": "播放音效",
        "template": 'AudioManager.play("effect_name")',
    },
    {
        "name": "AudioManager.play_music",
        "category": "音频",
        "description": "播放背景音乐",
        "template": 'AudioManager.play_music("sounds/bgm.ogg")',
    },
    # Scrawl V2 - Animation
    {
        "name": "Tween",
        "category": "动画",
        "description": "创建补间动画",
        "template": '''tween = Tween()
        tween.tween_property(self, "pos.x", target_value, 1.0)
        tween.play()''',
    },
    {
        "name": "AnimatedSprite2D",
        "category": "动画",
        "description": "帧动画精灵",
        "template": '''frames = SpriteFrames()
        frames.add_animation("walk")
        frames.add_frame("walk", "walk_1.png")
        frames.add_frame("walk", "walk_2.png")
        animated = AnimatedSprite2D(frames)
        animated.play("walk")''',
    },
    # Scrawl V2 - Camera
    {
        "name": "Camera2D",
        "category": "摄像机",
        "description": "创建摄像机跟随",
        "template": '''camera = Camera2D()
        camera.follow(self)
        camera.smoothing_enabled = True
        camera.smoothing_speed = 5.0''',
    },
    # Scrawl V2 - Timer
    {
        "name": "Timer",
        "category": "控制",
        "description": "定时器",
        "template": '''timer = Timer(wait_time=2.0, one_shot=True)
        timer.timeout.connect(self.on_timer_done)
        timer.start()''',
    },
    # Scrawl V2 - Particles
    {
        "name": "ParticleEmitter2D",
        "category": "特效",
        "description": "粒子发射器",
        "template": 'emitter = ParticleEmitter2D.create_preset("fire")',
    },
    # Scrawl V2 - State Machine
    {
        "name": "StateMachine",
        "category": "控制",
        "description": "状态机",
        "template": '''sm = StateMachine()
        sm.add_state("idle", IdleState())
        sm.add_state("walk", WalkState())
        sm.add_transition("idle", "walk", lambda: Input.is_action_pressed("move_right"))
        sm.start("idle")''',
    },
    # Scrawl V2 - Signals
    {
        "name": "Signal",
        "category": "信号",
        "description": "自定义信号",
        "template": '''# 类级别定义信号
    health_changed = Signal()

    # 连接信号
    self.health_changed.connect(self.on_health_changed)

    # 发射信号
    self.health_changed.emit(new_hp)''',
    },
    # Scrawl V2 - TileMap
    {
        "name": "TileMap",
        "category": "地图",
        "description": "创建瓦片地图",
        "template": '''tileset = TileSet(tile_size=32)
        tileset.add_tile(0, "tiles/grass.png")
        tileset.add_tile(1, "tiles/wall.png", has_collision=True)
        tilemap = TileMap(tileset)
        tilemap.load_from_string("""
        0 0 0 0
        0 1 1 0
        0 0 0 0
        """)''',
    },
    # Scrawl V2 - UI
    {
        "name": "Label",
        "category": "UI",
        "description": "文本标签",
        "template": '''label = Label("Score: 0")
        label.position = Vector2(10, 10)
        label.font_size = 24''',
    },
    {
        "name": "Button",
        "category": "UI",
        "description": "按钮",
        "template": '''btn = Button("Start")
        btn.pressed.connect(self.on_start_pressed)''',
    },
    {
        "name": "ProgressBar",
        "category": "UI",
        "description": "进度条",
        "template": '''hp_bar = ProgressBar()
        hp_bar.min_value = 0
        hp_bar.max_value = 100
        hp_bar.value = 100''',
    },
    # Scrawl V2 - Physics Bodies
    {
        "name": "RigidBody2D.apply_force",
        "category": "物理",
        "description": "刚体施加力",
        "template": '''self.apply_force(Vector2(0, -500))''',
    },
    {
        "name": "RigidBody2D.apply_impulse",
        "category": "物理",
        "description": "刚体施加冲量",
        "template": '''self.apply_impulse(Vector2(100, -200))''',
    },
    {
        "name": "KinematicBody2D.move",
        "category": "物理",
        "description": "运动学体移动（含碰撞）",
        "template": '''velocity = Vector2(0, 0)
        direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")
        velocity = direction * 200
        self.move_and_slide(velocity)''',
    },
    {
        "name": "Area2D.body_entered",
        "category": "物理",
        "description": "区域检测",
        "template": '''self.body_entered.connect(self.on_body_entered)

    def on_body_entered(self, body):
        print(f"进入区域: {body.name}")''',
    },
    {
        "name": "CollisionShape2D",
        "category": "物理",
        "description": "碰撞形状",
        "template": '''shape = CollisionShape2D()
        shape.set_rectangle(32, 32)
        # 或者圆形: shape.set_circle(16)
        self.add_child(shape)''',
    },
    # Scrawl V2 - Light2D
    {
        "name": "PointLight2D",
        "category": "渲染",
        "description": "点光源",
        "template": '''light = PointLight2D()
        light.color = Color(255, 200, 100)
        light.energy = 1.5
        light.radius = 300
        light.shadow_enabled = True''',
    },
    {
        "name": "DirectionalLight2D",
        "category": "渲染",
        "description": "平行光",
        "template": '''light = DirectionalLight2D()
        light.color = Color(255, 255, 200)
        light.energy = 0.8
        light.direction = 45''',
    },
    # Scrawl V2 - Navigation
    {
        "name": "NavigationAgent2D",
        "category": "寻路",
        "description": "导航代理",
        "template": '''agent = NavigationAgent2D()
        agent.max_speed = 200
        agent.set_target(Vector2(400, 300))
        # 主循环中调用:
        # velocity = agent.get_next_velocity()
        # self.pos += velocity * dt''',
    },
    {
        "name": "NavigationGrid",
        "category": "寻路",
        "description": "导航网格",
        "template": '''nav_grid = NavigationGrid(width=20, height=15, cell_size=32)
        nav_grid.set_obstacle(5, 3)
        path = nav_grid.find_path(start=(0, 0), end=(19, 14))''',
    },
    # Scrawl V2 - Path2D/Line2D
    {
        "name": "Path2D",
        "category": "路径",
        "description": "路径节点",
        "template": '''path = Path2D()
        path.add_point(Vector2(0, 0))
        path.add_point(Vector2(100, 50))
        path.add_point(Vector2(200, 0))''',
    },
    {
        "name": "PathFollow2D",
        "category": "路径",
        "description": "路径跟随",
        "template": '''follower = PathFollow2D()
        follower.path = path
        follower.speed = 100
        follower.loop = True''',
    },
    {
        "name": "Line2D",
        "category": "路径",
        "description": "绘制线条",
        "template": '''line = Line2D()
        line.add_point(Vector2(0, 0))
        line.add_point(Vector2(100, 100))
        line.width = 3
        line.color = Color(255, 0, 0)''',
    },
    # Scrawl V2 - ResourceLoader
    {
        "name": "ResourceLoader",
        "category": "资源",
        "description": "资源加载器",
        "template": '''# 预加载资源
        ResourceLoader.preload("player_sprite", "images/player.png")
        ResourceLoader.preload("jump_sound", "sounds/jump.ogg")
        
        # 获取资源
        img = ResourceLoader.get("player_sprite")''',
    },
    # Scrawl V2 - Panel
    {
        "name": "Panel",
        "category": "UI",
        "description": "面板容器",
        "template": '''panel = Panel()
        panel.position = Vector2(100, 100)
        panel.size = Vector2(200, 150)''',
    },
    # Scrawl V2 - CanvasLayer
    {
        "name": "CanvasLayer",
        "category": "UI",
        "description": "画布层（用于HUD）",
        "template": '''hud = CanvasLayer(layer=10)
        score_label = Label("Score: 0")
        hud.add_child(score_label)''',
    },
]


def get_decorator_categories() -> List[str]:
    """Get unique decorator categories."""
    categories = []
    for snippet in DECORATOR_SNIPPETS:
        cat = snippet.get("category", "其他")
        if cat not in categories:
            categories.append(cat)
    return categories


def get_function_categories() -> List[str]:
    """Get unique function categories."""
    categories = []
    for snippet in FUNCTION_SNIPPETS:
        cat = snippet.get("category", "其他")
        if cat not in categories:
            categories.append(cat)
    return categories


def get_decorators_by_category(category: str) -> List[Dict[str, Any]]:
    """Get decorators filtered by category."""
    return [s for s in DECORATOR_SNIPPETS if s.get("category") == category]


def get_functions_by_category(category: str) -> List[Dict[str, Any]]:
    """Get functions filtered by category."""
    return [s for s in FUNCTION_SNIPPETS if s.get("category") == category]
