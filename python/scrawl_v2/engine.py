"""
Game class - the main entry point for Scrawl v2 games.

Wraps the Bevy engine lifecycle. When native bridge is available,
delegates to the Rust engine. Otherwise falls back to a pure-Python stub.
"""

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

    def set_scene(self, scene):
        """Set the active scene."""
        self._active_scene = scene
        self._scenes.append(scene)

    def add_scene(self, scene):
        """Add a scene to the game (without making it active)."""
        self._scenes.append(scene)

    def switch_scene(self, scene_name: str):
        """Switch to a named scene."""
        for scene in self._scenes:
            if scene.name == scene_name:
                self._active_scene = scene
                break

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
