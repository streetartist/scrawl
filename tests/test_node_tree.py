import unittest

from scrawl import Game, Node, Node2D, PhysicsSprite, Scene, Sprite2D
from scrawl.node import _scrawl_command_queue


class NodeTreeTests(unittest.TestCase):
    def tearDown(self):
        _scrawl_command_queue.clear()

    def test_scene_records_are_parent_first_with_stable_unique_ids(self):
        scene = Scene("main")
        group = Node2D("group")
        player = Sprite2D()
        player.name = "player"

        scene.add_child(group)
        group.add_child(player)

        records = scene._scrawl_tree_records()
        self.assertEqual(
            [(parent_id, kind, node.name) for _, parent_id, kind, node in records],
            [
                (None, "scene", "main"),
                (scene._scrawl_node_id, "node2d", "group"),
                (group._scrawl_node_id, "sprite2d", "player"),
            ],
        )
        self.assertEqual(len({record[0] for record in records}), len(records))
        self.assertEqual(scene.sprites, [player])

    def test_add_child_rejects_invalid_cycles_and_duplicates(self):
        root = Node("root")
        child = Node("child")
        root.add_child(child)
        root.add_child(child)

        self.assertEqual(root.get_children(), [child])
        with self.assertRaises(TypeError):
            root.add_child(object())
        with self.assertRaises(ValueError):
            root.add_child(root)
        with self.assertRaises(ValueError):
            child.add_child(root)

    def test_reparent_propagates_scene_and_game_to_the_subtree(self):
        game = Game()
        first = Scene("first")
        second = Scene("second")
        branch = Node2D("branch")
        sprite = PhysicsSprite()
        branch.add_child(sprite)
        first.add_child(branch)
        game.set_scene(first)
        game.add_scene(second)

        self.assertIs(sprite.scene, first)
        self.assertIs(sprite.game, game)
        branch.reparent(second)
        self.assertIs(sprite.scene, second)
        self.assertIs(sprite.game, game)
        self.assertNotIn(sprite, first.sprites)
        self.assertIn(sprite, second.sprites)

    def test_clone_gets_a_new_node_id_and_keeps_the_parent(self):
        scene = Scene("main")
        group = Node2D("group")
        source = Sprite2D()
        scene.add_child(group)
        group.add_child(source)

        clone = source.clone()

        self.assertNotEqual(source._scrawl_node_id, clone._scrawl_node_id)
        self.assertIs(clone.get_parent(), group)
        self.assertEqual(scene.sprites, [source, clone])

    def test_runtime_tree_changes_use_unified_node_commands(self):
        game = Game()
        scene = Scene("main")
        first_parent = Node2D("first")
        second_parent = Node2D("second")
        scene.add_child(first_parent)
        scene.add_child(second_parent)
        game.set_scene(scene)
        game._native = object()

        child = Node2D("child")
        first_parent.add_child(child)
        child.reparent(second_parent)
        second_parent.remove_child(child)

        self.assertEqual(
            [command[0] for command in _scrawl_command_queue],
            ["node_add", "node_reparent", "node_remove"],
        )

    def test_runtime_clone_and_delete_share_the_node_lifecycle(self):
        game = Game()
        scene = Scene("main")
        source = Sprite2D()
        scene.add_child(source)
        game.set_scene(scene)
        game._native = object()

        clone = source.clone()
        clone.delete_self()

        self.assertEqual(
            [command[0] for command in _scrawl_command_queue],
            ["node_add", "node_remove"],
        )

    def test_node2d_dirty_state_is_consumed_once(self):
        node = Node2D("moving")
        self.assertFalse(node._take_node_dirty())

        node.position = (12, 34)
        node.rotation_degrees = 45
        node.scale = (2, 3)
        node.z_index = 4
        node.hide()

        self.assertTrue(node._take_node_dirty())
        self.assertFalse(node._take_node_dirty())

        node.position.x = 56
        self.assertTrue(node._take_node_dirty())
        node.scale.y = 4
        self.assertTrue(node._take_node_dirty())


if __name__ == "__main__":
    unittest.main()
