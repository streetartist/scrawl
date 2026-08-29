"""Native Rapier 2D demo: a circle falls onto a static rectangular floor."""

from scrawl import (
    CollisionShape2D,
    Game,
    RigidBody2D,
    Scene,
    Sprite2D,
    StaticBody2D,
    Vector2,
    on_key
)


class Ball(RigidBody2D):
    """A native rigid body with a collision shape and visual child."""

    def __init__(self):
        super().__init__("Ball")
        self.position = Vector2(400, 500)
        self.bounce = 0.45
        self.friction = 0.35

        shape = CollisionShape2D("BallShape")
        shape.set_circle(18)
        visual = Sprite2D()
        visual.name = "BallVisual"
        visual.position = Vector2(0, 0)
        visual.width = 36
        visual.height = 36
        visual.color = (238, 174, 76)
        self.add_child(shape)
        self.add_child(visual)

    @on_key("space", "pressed")
    def jump(self):
        # Scrawl's native 2D coordinates use +Y as up.
        self.apply_central_impulse(Vector2(0, 520))


class PhysicsScene(Scene):
    def __init__(self):
        super().__init__("native_physics")
        self.set_background_color(24, 29, 38)

        floor = StaticBody2D("Floor")
        # Scrawl uses a bottom-left origin, so the floor sits near y=40.
        floor.position = Vector2(400, 40)
        floor_shape = CollisionShape2D("FloorShape")
        floor_shape.set_rect(720, 24)
        floor_visual = Sprite2D()
        floor_visual.name = "FloorVisual"
        floor_visual.position = Vector2(0, 0)
        floor_visual.width = 720
        floor_visual.height = 24
        floor_visual.color = (90, 105, 125)
        floor.add_child(floor_shape)
        floor.add_child(floor_visual)
        self.add_child(floor)

        ball = Ball()
        self.add_child(ball)


game = Game(width=800, height=600, title="Scrawl - Native Physics")
game.set_scene(PhysicsScene())
print("Press SPACE to jump the ball.")
game.run()
