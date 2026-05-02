"""
Scene class - a container for sprites with a background.
"""

from .sprite import queue_broadcast

try:
    from scrawl_v2.scrawl_native import NativeScene
    _HAS_NATIVE = True
except ImportError:
    try:
        from scrawl_native import NativeScene
        _HAS_NATIVE = True
    except ImportError:
        _HAS_NATIVE = False


class Scene:
    """A game scene that contains sprites.

    Subclass this to create your game scenes:

        class MyScene(Scene):
            def __init__(self):
                super().__init__()
                self.add_sprite(Ball())
    """

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self._sprites = []
        self._background_color = (255, 255, 255)
        self._background_image = None
        self.game = None

        if _HAS_NATIVE:
            self._native = NativeScene(name=self.name)
        else:
            self._native = None

    def add_sprite(self, sprite):
        """Add a sprite to this scene."""
        self._sprites.append(sprite)
        sprite.scene = self
        sprite.game = self.game
        if self._native and hasattr(sprite, '_native'):
            self._native.add_sprite(sprite._native)

    def remove_sprite(self, sprite):
        """Remove a sprite from this scene."""
        self._sprites.remove(sprite)
        sprite.scene = None
        sprite.game = None

    def set_background_color(self, r: int = 255, g: int = 255, b: int = 255):
        """Set the background color."""
        self._background_color = (r, g, b)
        if self._native:
            self._native.set_background_color(r, g, b)

    def set_background_image(self, path: str):
        """Set a background image."""
        self._background_image = path
        if self._native:
            self._native.set_background_image(path)

    def broadcast(self, event: str):
        """Send a broadcast message to all sprites in this scene."""
        queue_broadcast(event)

    @property
    def sprites(self):
        """List of sprites in this scene."""
        return list(self._sprites)
