# Scrawl 2.2.0

- Made `scrawl` the only supported Python package.
- Removed the Pygame v1 engine, PygameGUI, legacy examples, and `scrawl_v2` compatibility package.
- Fixed native extension import initialization by using a direct package-relative import.
- Removed unused NativeScene and NativeSprite proxy classes.
- Added Sprite `width`, `height`, `set_dimensions()` and `z_index` support.
- Added dirty property synchronization and consolidated normal frame processing to one GIL acquisition.
- Reorganized current examples under `examples/` and replaced stale documentation.
