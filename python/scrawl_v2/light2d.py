"""
2D 光照系统 - 参考 Godot Light2D。

提供 2D 游戏中的光照效果。

用法:
    # 点光源（火把）
    torch_light = PointLight2D("TorchLight")
    torch_light.color = (255, 200, 100, 200)
    torch_light.energy = 1.0
    torch_light.range = 200
    torch.add_child(torch_light)

    # 方向光（阳光）
    sun = DirectionalLight2D("Sun")
    sun.color = (255, 255, 200, 100)
    sun.rotation_degrees = 45
"""

from .node import Node2D
from .math_utils import Vector2
from .signals import Signal


class Light2D(Node2D):
    """2D 光源基类 - 参考 Godot Light2D。"""

    # 混合模式
    BLEND_ADD = 0
    BLEND_SUB = 1
    BLEND_MIX = 2

    def __init__(self, name: str = "Light2D"):
        super().__init__(name)
        self.enabled = True
        self.color = (255, 255, 255, 255)
        self.energy = 1.0
        self.blend_mode = self.BLEND_ADD
        self.range_z_min = -1024
        self.range_z_max = 1024
        self.range_layer_min = 0
        self.range_layer_max = 512
        self.shadow_enabled = False
        self.shadow_color = (0, 0, 0, 128)
        self.texture = None
        self.texture_scale = 1.0


class PointLight2D(Light2D):
    """点光源 - 参考 Godot PointLight2D。

    从一个点向四周发出光线。
    """

    def __init__(self, name: str = "PointLight2D"):
        super().__init__(name)
        self.range = 100.0
        self.falloff = 1.0  # 衰减曲线 (1=线性)
        self.offset = Vector2()


class DirectionalLight2D(Light2D):
    """方向光 - 参考 Godot DirectionalLight2D。

    平行光源，模拟远处光源如阳光。
    """

    def __init__(self, name: str = "DirectionalLight2D"):
        super().__init__(name)
        self.max_distance = 10000.0


class LightOccluder2D(Node2D):
    """光照遮挡器 - 参考 Godot LightOccluder2D。

    阻挡 Light2D 的光线，产生阴影。
    """

    def __init__(self, name: str = "LightOccluder2D"):
        super().__init__(name)
        self.polygon: list = []  # Vector2 点列表
        self.occluder_light_mask = 1


class CanvasModulate(Node2D):
    """画布调色 - 参考 Godot CanvasModulate。

    用于设置环境光颜色，配合 Light2D 创建黑暗环境。
    """

    def __init__(self, name: str = "CanvasModulate"):
        super().__init__(name)
        self.color = (50, 50, 80, 255)  # 环境光颜色（暗色=黑暗环境）
