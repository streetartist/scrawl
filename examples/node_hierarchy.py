"""Node2D hierarchy example for the unified scene-tree bridge."""

from scrawl import Game, Node2D, Scene, Sprite, as_main


class OrbitingTile(Sprite):
    def __init__(self, name, x, color):
        super().__init__()
        self.name = name
        self.x = x
        self.y = 0
        self.color = color
        self.set_dimensions(56, 56)

    @as_main
    def animate(self):
        while True:
            self.turn_right(2)
            yield 16


class HierarchyController(Sprite):
    def __init__(self):
        super().__init__()
        self.name = "hierarchy-controller"
        self.visible = False
        self.set_dimensions(1, 1)

    @as_main
    def add_runtime_node(self):
        # This runs after startup, exercising node_add and Node2D property sync.
        yield 1200
        marker = Node2D("runtime-marker")
        marker.position = (0, 96)
        marker.scale = (0.7, 0.7)
        marker.add_child(OrbitingTile("runtime-tile", 0, (245, 200, 66)))
        group = self.scene.get_node("center-group")
        group.add_child(marker)
        yield 900
        marker.position = (0, 140)
        yield 900
        marker.reparent(self.scene)
        yield 900
        marker.queue_free()


class HierarchyScene(Scene):
    def __init__(self):
        super().__init__("hierarchy")
        self.set_background_color(25, 32, 43)

        group = Node2D("center-group")
        group.position = (400, 300)
        group.add_child(OrbitingTile("left", -72, (84, 193, 189)))
        group.add_child(OrbitingTile("right", 72, (240, 106, 95)))
        self.add_child(HierarchyController())
        self.add_child(group)


game = Game(width=800, height=600, title="Scrawl Node Hierarchy")
game.set_scene(HierarchyScene())
game.run(fps=60, debug=True)
