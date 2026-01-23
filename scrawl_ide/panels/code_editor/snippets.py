"""
Code Snippets for Scrawl IDE

Defines decorator and function templates for quick insertion.
"""

from typing import List, Dict, Any


# Decorator snippets
DECORATOR_SNIPPETS: List[Dict[str, Any]] = [
    {
        "name": "@on_key",
        "category": "事件",
        "description": "键盘按键事件",
        "template": '''@on_key(pygame.K_SPACE, "pressed")
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
        "template": "if self.is_key_pressed(pygame.K_SPACE):",
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
