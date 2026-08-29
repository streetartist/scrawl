# Runtime Roadmap

This file tracks gaps between the public Python data model and the Rust NativeGame runtime.

## P0: unified node bridge

- [x] Make `Scene` the Node tree root and traverse it in parent-first order.
- [x] Create registered ECS entities for Scene, Node, Node2D and Sprite nodes at startup.
- [x] Map initial Node2D transforms, visibility and hierarchy to Bevy entities.
- [x] Synchronize Node2D transform, z-index and visibility changes after the game loop starts.
- [x] Define creation, deletion and same-scene reparenting commands for runtime nodes.
- [x] Migrate clone/delete commands onto the unified node lifecycle.

## P1: feature mappings

- Map physics bodies and collision shapes to Rapier entities.
- Map Control, Label, Button and layout containers to `scrawl-ui`.
- Map TileMap, ParticleEmitter2D and navigation nodes to their plugins.
- Add camera, light and path runtime mappings.

## P2: runtime architecture

- Move the Python command queue into a per-Game bridge context.
- Add a supported background-task/result API for model inference and I/O.
- Add capability introspection and runtime contract tests for every exported node type.
- Enable the complete plugin set in the standalone app after mappings are tested.
