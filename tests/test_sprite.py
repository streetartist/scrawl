import unittest

from scrawl import Sprite, on_key
from scrawl.sprite import (
    _DIRTY_COLOR,
    _DIRTY_DIMENSIONS,
    _DIRTY_DRAW_ORDER,
    _DIRTY_TRANSFORM,
    _DIRTY_VISIBLE,
)


class SpriteStateTests(unittest.TestCase):
    def setUp(self):
        self.sprite = Sprite()
        self.sprite._take_dirty()

    def test_transform_mutations_are_tracked(self):
        self.sprite.position = (10, 300)
        self.assertEqual((self.sprite.position.x, self.sprite.position.y), (10, 300))
        self.sprite._take_dirty()
        self.sprite.x = 10
        self.sprite.move_up(4)
        self.assertEqual(self.sprite._take_dirty(), _DIRTY_TRANSFORM)
        self.assertEqual((self.sprite.x, self.sprite.y), (10, 304))

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

    def test_key_decorator_rejects_integer_constants(self):
        with self.assertRaises(TypeError):
            on_key(32)(lambda self: None)


if __name__ == "__main__":
    unittest.main()
