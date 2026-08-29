"""Scene tree root with a background and Sprite convenience methods."""

from .node import Node
from .sprite import queue_broadcast


class Scene(Node):
    """A game scene that contains sprites.

    Subclass this to create your game scenes:

        class MyScene(Scene):
            def __init__(self):
                super().__init__()
                self.add_sprite(Ball())
    """

    def __init__(self, name: str = None):
        super().__init__(name or self.__class__.__name__)
        self._scrawl_node_kind = "scene"
        self._background_color = (255, 255, 255)
        self._background_image = None
        self._set_scene(self)

    def add_sprite(self, sprite):
        """Add a Sprite as a direct child of this scene."""
        if getattr(sprite, "_scrawl_node_kind", None) != "sprite":
            raise TypeError("add_sprite expects a Sprite or PhysicsSprite")
        self.add_child(sprite)

    def remove_sprite(self, sprite):
        """Remove a sprite from this scene."""
        parent = sprite.get_parent()
        if parent is not None:
            parent.remove_child(sprite)

    def set_background_color(self, r: int = 255, g: int = 255, b: int = 255):
        """Set the background color."""
        self._background_color = (r, g, b)

    def set_background_image(self, path: str):
        """Set a background image."""
        self._background_image = path

    def broadcast(self, event: str):
        """Send a broadcast message to all sprites in this scene."""
        queue_broadcast(event)

    @property
    def sprites(self):
        """All Sprite descendants in deterministic tree order."""
        return [
            node
            for node in self.iter_tree(include_self=False)
            if getattr(node, "_scrawl_node_kind", None) == "sprite"
        ]
