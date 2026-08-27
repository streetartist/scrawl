# Migrating to Scrawl 2.2

Scrawl 2.2 makes the Rust/Bevy engine the only implementation.

## Package imports

Replace every old import:

```python
from scrawl_v2 import Game, Scene, Sprite
```

with:

```python
from scrawl import Game, Scene, Sprite
```

`scrawl_v2` is not installed and intentionally raises `ModuleNotFoundError`.

## Pygame removal

- Pass image paths to `Sprite.add_costume()` instead of Pygame Surface objects.
- Use string keys such as `"space"` and `"left"` in `@on_key`.
- Use tuples or Scrawl `Vector2` values for positions.
- PygameGUI, Cat, TkGUI, cloud variables and the Pygame utility module were v1-only and have been removed.

## New Sprite layout API

```python
sprite.set_dimensions(160, 48)
sprite.z_index = 10
```

`size` remains a uniform scale. `width` and `height` set the base render dimensions.
