# Scrawl Runtime Manual

## Public package

Use only `scrawl`:

```python
from scrawl import Game, Scene, Sprite, as_main, on_key
```

There is no `scrawl_v2` compatibility package and no Pygame backend.

## Core lifecycle

1. Subclass `Sprite` and attach decorated event handlers.
2. Build a Scene tree with `add_child()`, or use `add_sprite()` for direct Sprite children.
3. Attach the Scene to `Game` with `set_scene()`.
4. Call `game.run()` to enter the Rust/Bevy loop.

Handlers may be normal functions or generators. A yielded number is a delay in milliseconds.

```python
class Ball(Sprite):
    @as_main
    def move_forever(self):
        while True:
            self.move(3)
            yield 16
```

## Scene tree

`Scene`, `Node`, `Node2D` and `Sprite` now share one Python tree. The native bridge traverses the tree in deterministic parent-before-child order and creates the matching Bevy entity hierarchy at startup.

```python
from scrawl import Node2D, Scene, Sprite


scene = Scene("main")
group = Node2D("group")
group.position = (400, 300)

player = Sprite()
player.pos = (40, 0)  # local to group

group.add_child(player)
scene.add_child(group)
```

Every Node receives a stable `_scrawl_node_id` used internally by the bridge. User code should use Node references and paths rather than depending on that private identifier.

At this stage, the tree is mapped when `game.run()` starts. Runtime `add_child()`, `remove_child()` and `reparent()` synchronization is the next bridge milestone; mutating the Python tree while the window is running does not yet create or move generic native entities.

## Sprite properties

| Property | Meaning |
| --- | --- |
| `x`, `y`, `pos` | World position, using a bottom-left origin |
| `direction` | Compass degrees: 0 up, 90 right |
| `size` | Uniform scale |
| `width`, `height` | Optional explicit render dimensions in pixels |
| `z_index` | Draw order; larger values render above smaller values |
| `visible` | Native visibility |
| `color` | RGB color for shape sprites |
| `collision_type` | `rect`, `circle`, or `mask` |

Costumes must be filesystem paths:

```python
self.add_costume("idle", "assets/player.png")
self.switch_costume("idle")
```

## Events

```python
@on_key("left", "held")
def move_left(self):
    self.move_left(4)

@on_mouse(1, "pressed")
def click(self):
    self.say("clicked")

@on_broadcast("reset")
def reset(self):
    self.go_to(400, 300)

@on_sprite_clicked
def selected(self):
    self.color = (255, 200, 80)

@on_edge_collision("any")
def bounce(self):
    self.turn_right(180)

@on_sprite_collision("Enemy")
def hit_enemy(self):
    self.delete_self()
```

Key identifiers are strings. Integer Pygame constants are intentionally rejected.

## Native runtime status

| Capability | Status |
| --- | --- |
| Game, Scene and Sprite startup | Connected |
| Keyboard, mouse and sprite click events | Connected |
| Broadcast, clone and delete | Connected |
| Transform, dimensions, draw order, color, visibility and costume sync | Connected |
| Edge, rectangle, circle and mask collision | Connected |
| Persistent text and speech | Connected |
| Pen drawing | Connected |
| Sound effects and music | Connected |
| Scene / Node / Node2D startup hierarchy | Connected |
| Runtime Node creation, deletion and same-scene reparenting | Connected |
| Physics Node mapping | Partial / experimental |
| UI Node mapping | Python model only |
| TileMap, Particles and Navigation mapping | Python model only |

An importable Python class does not imply NativeGame integration. Remaining mappings are tracked in [ROADMAP.md](ROADMAP.md).

## Performance model

The bridge acquires the GIL once during a normal fixed-update frame. Each Sprite exposes a dirty bitset and each Node2D exposes a transform dirty flag, so unchanged properties are not repeatedly extracted from Python. Script work is bounded by the runtime frame budget; long AI inference or blocking I/O should run outside event handlers and return results through a queue.
