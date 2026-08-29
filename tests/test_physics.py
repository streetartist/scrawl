import unittest

from scrawl import (
    CircleShape2D,
    CollisionShape2D,
    KinematicBody2D,
    RigidBody2D,
    Scene,
    StaticBody2D,
    Vector2,
    on_key,
)


class PhysicsNodeTests(unittest.TestCase):
    def test_native_kinds_and_shape_records_are_structured(self):
        scene = Scene("physics")
        ground = StaticBody2D("ground")
        shape = CollisionShape2D("ground_shape")
        shape.set_rect(640, 24)
        ground.add_child(shape)
        ball = RigidBody2D("ball")
        ball.position = Vector2(120, 40)
        ball.linear_velocity = Vector2(0, 10)
        ball_shape = CollisionShape2D("ball_shape")
        ball_shape.set_circle(12)
        ball.add_child(ball_shape)
        player = KinematicBody2D("player")
        scene.add_child(ground)
        scene.add_child(ball)
        scene.add_child(player)

        records = scene._scrawl_tree_records()
        self.assertEqual(
            [record[2] for record in records],
            [
                "scene",
                "static_body2d",
                "collision_shape2d",
                "rigid_body2d",
                "collision_shape2d",
                "kinematic_body2d",
            ],
        )
        self.assertEqual(ball_shape.shape.radius, 12)
        self.assertEqual(shape.shape.size.x, 640)

    def test_native_sync_does_not_mark_python_state_dirty(self):
        body = RigidBody2D("ball")
        body._scrawl_sync_physics_state(8, 9, 15, 1, 2, 0.5)
        self.assertEqual((body.position.x, body.position.y), (8, 9))
        self.assertAlmostEqual(body.rotation_degrees, 15)
        self.assertEqual((body.linear_velocity.x, body.linear_velocity.y), (1, 2))
        self.assertFalse(body._take_node_dirty())

    def test_shape_mutations_mark_native_state_dirty(self):
        shape = CollisionShape2D("shape")
        shape._take_node_dirty()
        shape.set_circle(18)
        self.assertTrue(shape._take_node_dirty())
        shape.disabled = True
        self.assertTrue(shape._take_node_dirty())

    def test_physics_shapes_and_properties_reject_non_finite_values(self):
        with self.assertRaises(ValueError):
            CircleShape2D(float("nan"))
        with self.assertRaises(ValueError):
            RigidBody2D("ball").gravity_scale = float("inf")

    def test_native_rigidbody_does_not_run_fallback_gravity(self):
        body = RigidBody2D("ball")
        body.position = Vector2(10, 20)
        body._take_node_dirty()

        class NativeGame:
            _native = object()

        body.game = NativeGame()
        body._physics_process(1.0)
        self.assertEqual((body.position.x, body.position.y), (10, 20))

    def test_native_rigidbody_can_own_input_handlers(self):
        class PlayerBody(RigidBody2D):
            @on_key("space", "pressed")
            def jump(self):
                self.apply_central_impulse(Vector2(0, 520))

        body = PlayerBody()
        self.assertEqual(PlayerBody.jump._key_event, ("space", "pressed"))
        body.jump()
        self.assertEqual((body.linear_velocity.x, body.linear_velocity.y), (0, 520))

    def test_kinematic_motion_marks_native_transform_dirty(self):
        body = KinematicBody2D("player")
        body._take_node_dirty()
        body.velocity = Vector2(60, 0)
        body.move_and_slide()
        self.assertEqual((body.position.x, body.position.y), (1, 0))
        self.assertTrue(body._take_node_dirty())


if __name__ == "__main__":
    unittest.main()
