"""
Default game script template.
"""

from scrawl import *


class Player(Sprite):
    """Player sprite."""

    def __init__(self):
        super().__init__()
        # Add your costumes here
        # self.add_costume("assets/images/player.png")

    def on_start(self):
        """Called when the game starts."""
        self.go_to(400, 300)

    def on_update(self):
        """Called every frame."""
        # Movement with arrow keys
        if key_pressed("up"):
            self.move(5)
        if key_pressed("down"):
            self.move(-5)
        if key_pressed("left"):
            self.turn_left(5)
        if key_pressed("right"):
            self.turn_right(5)


def setup():
    """Set up the game."""
    set_background_color(100, 150, 200)

    player = Player()


if __name__ == "__main__":
    game = Game(800, 600, "My Scrawl Game")
    setup()
    game.run()
