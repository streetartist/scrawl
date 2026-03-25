//! Core events for the Scrawl engine.

use bevy::prelude::*;

/// A broadcast message sent to all sprites in the current scene.
#[derive(Event, Debug, Clone)]
pub struct BroadcastEvent(pub String);

/// Fired when a sprite touches a screen edge.
#[derive(Event, Debug, Clone)]
pub struct EdgeCollisionEvent {
    pub entity: Entity,
    pub edge: Edge,
}

/// Screen edge identifier.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Edge {
    Left,
    Right,
    Top,
    Bottom,
}

/// Fired when two sprites collide.
#[derive(Event, Debug, Clone)]
pub struct SpriteCollisionEvent {
    pub entity_a: Entity,
    pub entity_b: Entity,
}

/// Keyboard input event (processed version).
#[derive(Event, Debug, Clone)]
pub struct KeyInputEvent {
    pub key: KeyCode,
    pub mode: InputMode,
}

/// Mouse input event (processed version).
#[derive(Event, Debug, Clone)]
pub struct MouseInputEvent {
    pub button: MouseButton,
    pub mode: InputMode,
    pub position: Vec2,
}

/// Input event mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InputMode {
    Pressed,
    Released,
    Held,
}

/// Fired when a sprite is clicked.
#[derive(Event, Debug, Clone)]
pub struct SpriteClickedEvent(pub Entity);

/// Request to change the active scene.
#[derive(Event, Debug, Clone)]
pub struct SceneChangeEvent {
    pub scene_name: String,
}
