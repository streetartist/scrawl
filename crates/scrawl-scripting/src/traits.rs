//! The ScrawlScript trait - the Rust scripting API.
//!
//! Users implement this trait to write game logic in pure Rust.
//! The API mirrors the Python Sprite API for consistency.

use bevy::prelude::*;

use crate::context::ScriptContext;

/// Input event mode (mirrors Python API's "pressed"/"released"/"held").
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InputMode {
    Pressed,
    Released,
    Held,
}

/// Screen edge identifier.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ScriptEdge {
    Left,
    Right,
    Top,
    Bottom,
}

/// The trait that Rust game scripts implement.
///
/// All methods have default no-op implementations, so users only
/// override what they need.
///
/// # Example
/// ```ignore
/// struct Ball;
///
/// impl ScrawlScript for Ball {
///     fn on_start(&mut self, ctx: &mut ScriptContext) {
///         ctx.set_costume("ball");
///     }
///
///     fn on_update(&mut self, ctx: &mut ScriptContext) {
///         ctx.move_steps(5.0);
///         ctx.turn_right(1.0);
///     }
///
///     fn on_key(&mut self, ctx: &mut ScriptContext, key: KeyCode, mode: InputMode) {
///         if key == KeyCode::Space && mode == InputMode::Pressed {
///             ctx.broadcast("jump");
///         }
///     }
/// }
/// ```
pub trait ScrawlScript: Send + Sync + 'static {
    /// Called once when the entity is spawned.
    fn on_start(&mut self, _ctx: &mut ScriptContext) {}

    /// Called every frame.
    fn on_update(&mut self, _ctx: &mut ScriptContext) {}

    /// Called on keyboard events.
    fn on_key(&mut self, _ctx: &mut ScriptContext, _key: KeyCode, _mode: InputMode) {}

    /// Called when a broadcast message is received.
    fn on_broadcast(&mut self, _ctx: &mut ScriptContext, _event: &str) {}

    /// Called when this entity collides with another entity.
    fn on_collision(&mut self, _ctx: &mut ScriptContext, _other: Entity) {}

    /// Called when this entity touches a screen edge.
    fn on_edge_collision(&mut self, _ctx: &mut ScriptContext, _edge: ScriptEdge) {}

    /// Called on mouse events.
    fn on_mouse(&mut self, _ctx: &mut ScriptContext, _button: MouseButton, _mode: InputMode) {}

    /// Called when this sprite is clicked.
    fn on_clicked(&mut self, _ctx: &mut ScriptContext) {}

    /// Called when this entity is cloned. The context refers to the new clone.
    fn on_clone(&mut self, _ctx: &mut ScriptContext) {}
}
