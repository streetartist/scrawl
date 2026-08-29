"""Native Rapier 2D demo: a circle falls onto a static rectangular floor."""

from scrawl import (
    CollisionShape2D,
    Game,
    RigidBody2D,
    Scene,
    Sprite,
    StaticBody2D,
    Vector2,
)


class PhysicsScene(Scene):
    def __init__(self):
        super().__init__("native_physics")
        self.set_background_color(24, 29, 38)

        floor = StaticBody2D("Floor")
        # Scrawl uses a bottom-left origin, so the floor sits near y=40.
        floor.position = Vector2(400, 40)
        floor_shape = CollisionShape2D("FloorShape")
        floor_shape.set_rect(720, 24)
        floor_visual = Sprite()
        floor_visual.name = "FloorVisual"
        floor_visual.position = Vector2(0, 0)
        floor_visual.width = 720
        floor_visual.height = 24
        floor_visual.color = (90, 105, 125)
        floor.add_child(floor_shape)
        floor.add_child(floor_visual)
        self.add_child(floor)

        ball = RigidBody2D("Ball")
        ball.position = Vector2(400, 500)
        ball.bounce = 0.45
        ball.friction = 0.35
        ball_shape = CollisionShape2D("BallShape")
        ball_shape.set_circle(18)
        ball_visual = Sprite()
        ball_visual.name = "BallVisual"
        ball_visual.position = Vector2(0, 0)
        ball_visual.width = 36
        ball_visual.height = 36
        ball_visual.size = 1
        ball_visual.color = (238, 174, 76)
        ball.add_child(ball_shape)
        ball.add_child(ball_visual)
        self.add_child(ball)


game = Game(width=800, height=600, title="Scrawl - Native Physics")
game.set_scene(PhysicsScene())
game.run()
