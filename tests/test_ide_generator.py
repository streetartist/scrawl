import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrawl_ide"))

from models import ProjectModel, SceneModel, SpriteModel
from runner.code_generator import CodeGenerator


class IdeGeneratorTests(unittest.TestCase):
    def _generate(self, node_type):
        project = ProjectModel(
            name="generator-test",
            scenes=[SceneModel.create_default("Main")],
        )
        sprite = SpriteModel.create_default("Ball", node_type)
        project.scenes[0].add_sprite(sprite)
        return CodeGenerator(project, ".").generate_main()

    def test_sprite2d_uses_node_tree_api(self):
        code = self._generate("Sprite2D")
        self.assertNotRegex(code, r"\.pos\b")
        self.assertIn("ball.position = (400.0, 300.0)", code)
        self.assertIn("self.add_child(ball)", code)
        ast.parse(code)

    def test_rigidbody_uses_composed_collision_shape(self):
        code = self._generate("RigidBody2D")
        self.assertIn("CollisionShape2D()", code)
        self.assertIn("_collision_shape.set_rect", code)
        self.assertNotIn("set_gravity", code)
        self.assertNotIn("set_elasticity", code)
        self.assertNotIn("PhysicsSprite", code)
        ast.parse(code)

    def test_legacy_physics_sprite_models_are_normalized(self):
        model = SpriteModel.from_dict({
            "name": "LegacyBall",
            "class": "LegacyBall",
            "node_type": "PhysicsSprite",
            "is_physics": True,
        })
        self.assertEqual(model.node_type, "RigidBody2D")
        self.assertTrue(model.is_physics)


if __name__ == "__main__":
    unittest.main()
