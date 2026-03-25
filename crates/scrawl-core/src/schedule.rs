//! System set definitions for ordering Scrawl engine systems.

use bevy::prelude::*;

/// System sets that define the execution order of Scrawl engine systems.
///
/// Systems are executed in this order each frame:
/// Input → ScriptExec → Physics → CollisionDetect → Animation → Particles → Navigation → PostUpdate
///
/// Bevy's built-in rendering happens after all Update systems.
#[derive(SystemSet, Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ScrawlSet {
    /// Gather keyboard/mouse input, update MouseState, fire KeyInputEvents.
    Input,
    /// Execute Python and Rust scripts (advance coroutines).
    ScriptExec,
    /// Physics simulation step (Rapier2D).
    Physics,
    /// Detect edge and sprite collisions, fire collision events.
    CollisionDetect,
    /// Update animations, tweens, sprite sheet playback.
    Animation,
    /// Update GPU particle systems.
    Particles,
    /// Pathfinding and navigation updates.
    Navigation,
    /// Cleanup: reset broadcast queue, remove expired entities, etc.
    PostUpdate,
}
