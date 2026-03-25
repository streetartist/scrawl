"""
Compatibility layer for scrawl v1 API.

Provides shims so that existing v1 code can run with minimal changes.
"""


def ensure_v1_compat():
    """Set up v1 compatibility mode.

    Call this to enable backward-compatible behavior:
    - pygame.K_* constants work in @on_key decorators
    - pygame.Surface costumes are auto-converted
    - Old GUIManager API is wrapped
    """
    pass  # TODO: implement as needed during migration


class GUIManagerCompat:
    """Compatibility shim for the v1 GUIManager class.

    Wraps the new scrawl-ui system with the old GUIManager API.
    """

    def __init__(self):
        self._buttons = []
        self._labels = []

    def create_button(self, x, y, width, height, text, callback=None, **kwargs):
        """Create a button (v1 compat)."""
        # TODO: delegate to scrawl-ui when available
        pass

    def create_label(self, x, y, text, **kwargs):
        """Create a label (v1 compat)."""
        pass

    def update(self, events=None):
        """Update GUI elements (v1 compat)."""
        pass

    def draw(self, surface=None):
        """Draw GUI elements (v1 compat)."""
        pass
