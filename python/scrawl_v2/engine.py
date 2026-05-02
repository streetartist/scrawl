"""
Game class - the main entry point for Scrawl v2 games.

Wraps the Bevy engine lifecycle. When native bridge is available,
delegates to the Rust engine. Otherwise falls back to a pure-Python stub.
"""

from .sprite import (
    queue_pause_music,
    queue_play_music,
    queue_play_sound,
    queue_resume_music,
    queue_stop_music,
)

try:
    from scrawl.scrawl_native import NativeGame
    _HAS_NATIVE = True
except ImportError:
    try:
        from scrawl_v2.scrawl_native import NativeGame
        _HAS_NATIVE = True
    except ImportError:
        try:
            from scrawl_native import NativeGame
            _HAS_NATIVE = True
        except ImportError:
            _HAS_NATIVE = False


class Game:
    """The main game controller.

    Creates a window and runs the game loop.

    Args:
        width: Window width in pixels (default: 800)
        height: Window height in pixels (default: 600)
        title: Window title
        fps: Target frames per second (default: 60)
        fullscreen: Whether to run in fullscreen mode
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Scrawl Game",
        fps: int = 60,
        fullscreen: bool = False,
    ):
        self.width = width
        self.height = height
        self.title = title
        self.fps = fps
        self.fullscreen = fullscreen

        self._scenes = []
        self._active_scene = None
        self._native = None
        self._sound_effects = {}
        self._music = {}

    def _attach_scene(self, scene):
        scene.game = self
        for sprite in scene.sprites:
            sprite.game = self

    def set_scene(self, scene):
        """Set the active scene."""
        self._attach_scene(scene)
        self._active_scene = scene
        self._scenes.append(scene)

    def add_scene(self, scene):
        """Add a scene to the game (without making it active)."""
        self._attach_scene(scene)
        self._scenes.append(scene)

    def switch_scene(self, scene_name: str):
        """Switch to a named scene."""
        for scene in self._scenes:
            if scene.name == scene_name:
                self._attach_scene(scene)
                self._active_scene = scene
                break

    def load_sound(self, name: str, file_path: str):
        """Register a named sound effect."""
        self._sound_effects[name] = file_path

    def load_music(self, name: str, file_path: str):
        """Register a named music track."""
        self._music[name] = file_path

    def play_sound(self, name: str, volume: float = None):
        """Play a registered sound effect or direct file path."""
        path = self._sound_effects.get(name, name)
        queue_play_sound(path, volume)

    def play_music(self, name: str, loops: int = -1, volume: float = None):
        """Play a registered music track or direct file path."""
        path = self._music.get(name, name)
        queue_play_music(path, loops, volume)

    def stop_music(self):
        """Stop background music."""
        queue_stop_music()

    def pause_music(self):
        """Pause background music."""
        queue_pause_music()

    def unpause_music(self):
        """Resume background music."""
        queue_resume_music()

    def run(self, fps: int = None, debug: bool = False, vsync: bool = True):
        """Start the game loop. Blocks until the window is closed.

        Args:
            fps: Override the game logic FPS (FixedUpdate rate, default: 60)
            debug: Whether to enable debug overlays (default: False)
            vsync: Whether to sync rendering to monitor refresh rate (default: True)
        """
        if fps is not None:
            self.fps = fps

        if not _HAS_NATIVE:
            print(f"[Scrawl 2.0] Native engine not available.")
            print(f"[Scrawl 2.0] Build scrawl-bridge with: maturin develop")
            print(f"[Scrawl 2.0] Game: {self.title} ({self.width}x{self.height} @ {self.fps}fps)")
            return

        # Create native game at run time so debug is known
        native = NativeGame(
            width=self.width,
            height=self.height,
            title=self.title,
            fps=self.fps,
            fullscreen=self.fullscreen,
            debug=debug,
            vsync=vsync,
        )

        # Pass the active scene
        if self._active_scene is not None:
            native.set_scene(self._active_scene)
        else:
            raise RuntimeError("No scene set. Call game.set_scene() first.")

        native.run()

    @property
    def screen_width(self) -> int:
        return self.width

    @property
    def screen_height(self) -> int:
        return self.height
