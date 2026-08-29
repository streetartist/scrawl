import unittest

from scrawl import Node2D, Sprite2D, on_key
from scrawl.sprite import (
    _DIRTY_COLOR,
    _DIRTY_DIMENSIONS,
    _DIRTY_DRAW_ORDER,
    _DIRTY_TRANSFORM,
    _DIRTY_VISIBLE,
)


class SpriteStateTests(unittest.TestCase):
    def setUp(self):
        self.sprite = Sprite2D()
        self.sprite._take_dirty()

    def test_transform_mutations_are_tracked(self):
        self.sprite.position = (10, 300)
        self.assertEqual((self.sprite.position.x, self.sprite.position.y), (10, 300))
        self.sprite._take_dirty()
        self.sprite.x = 10
        self.sprite.move_up(4)
        self.assertEqual(self.sprite._take_dirty(), _DIRTY_TRANSFORM)
        self.assertEqual((self.sprite.x, self.sprite.y), (10, 304))

    def test_sprite2d_is_a_node2d_with_unified_transform_aliases(self):
        self.assertIsInstance(self.sprite, Node2D)
        self.assertEqual(self.sprite._scrawl_node_kind, "sprite2d")
        self.assertEqual(self.sprite.direction, 90)

        self.sprite.scale = (2, 3)
        self.assertEqual((self.sprite.scale.x, self.sprite.scale.y), (2, 3))
        self.sprite.size = 4
        self.assertEqual((self.sprite.scale.x, self.sprite.scale.y), (4, 4))

        self.sprite.rotation_degrees = 90
        self.assertEqual(self.sprite.direction, 0)
        self.sprite.direction = 180
        self.assertEqual(self.sprite.rotation_degrees, -90)

    def test_sprite2d_accepts_godot_name_and_uses_local_origin(self):
        named = Sprite2D("player")
        self.assertEqual(named.name, "player")
        self.assertEqual((named.position.x, named.position.y), (0, 0))

    def test_global_position_composes_parent_rotation_and_scale(self):
        parent = Node2D("parent")
        child = Sprite2D("child")
        parent.position = (100, 50)
        parent.rotation_degrees = 90
        parent.scale = (2, 2)
        child.position = (10, 0)
        parent.add_child(child)

        self.assertAlmostEqual(child.global_position.x, 100)
        self.assertAlmostEqual(child.global_position.y, 70)
        child.global_position = (100, 90)
        self.assertAlmostEqual(child.position.x, 20)
        self.assertAlmostEqual(child.position.y, 0)

    def test_render_properties_are_tracked_independently(self):
        self.sprite.color = (1, 2, 3)
        self.sprite.visible = False
        self.sprite.set_dimensions(120, 40)
        self.sprite.z_index = 7
        self.assertEqual(
            self.sprite._take_dirty(),
            _DIRTY_COLOR | _DIRTY_VISIBLE | _DIRTY_DIMENSIONS | _DIRTY_DRAW_ORDER,
        )

    def test_costume_requires_a_path(self):
        with self.assertRaises(TypeError):
            self.sprite.add_costume("bad", object())

    def test_transform_and_dimensions_reject_non_finite_values(self):
        with self.assertRaises(ValueError):
            self.sprite.position = (float("nan"), 0)
        with self.assertRaises(ValueError):
            self.sprite.scale = (1, float("inf"))
        with self.assertRaises(ValueError):
            self.sprite.set_dimensions(float("nan"), 10)

    def test_key_decorator_rejects_integer_constants(self):
        with self.assertRaises(TypeError):
            on_key(32)(lambda self: None)


if __name__ == "__main__":
    unittest.main()
