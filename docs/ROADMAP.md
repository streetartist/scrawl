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

- [x] Map StaticBody2D, RigidBody2D, KinematicBody2D and rectangle/circle CollisionShape2D nodes to Rapier entities.
- [x] Sync native physics transforms and velocities back to Python, including runtime node additions.
- Map native capsule, polygon and mask shapes without an AABB fallback.
- Map Area2D, RayCast2D, collision signals and query APIs.
- Map Control, Label, Button and layout containers to `scrawl-ui`.
- Map TileMap, ParticleEmitter2D and navigation nodes to their plugins.
- Add camera, light and path runtime mappings.

## P2: runtime architecture

- Move the Python command queue into a per-Game bridge context.
- Add a supported background-task/result API for model inference, I/O and so on.
- Add capability introspection and runtime contract tests for every exported node type.
- Enable the complete plugin set in the standalone app after mappings are tested.
