//! Scrawl Editor Protocol - IPC message definitions for IDE↔Engine communication.
//!
//! Messages are serialized with MessagePack (rmp-serde) for compact binary IPC.

use serde::{Deserialize, Serialize};

/// Messages from the IDE to the engine.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IdeToEngine {
    /// Load a project from JSON data.
    LoadProject { json: String },
    /// Spawn an entity in the current scene.
    SpawnEntity {
        name: String,
        x: f32,
        y: f32,
        sprite_path: Option<String>,
    },
    /// Update an entity's transform.
    UpdateEntityTransform {
        entity_id: u64,
        x: f32,
        y: f32,
        rotation: f32,
        scale: f32,
    },
    /// Delete an entity.
    DeleteEntity { entity_id: u64 },
    /// Set the scene background.
    SetBackground {
        color: [u8; 3],
        image_path: Option<String>,
    },
    /// Start playing the game.
    Play,
    /// Pause the game.
    Pause,
    /// Stop the game and reset to saved state.
    Stop,
    /// Advance a single frame (debug).
    StepFrame,
    /// Reload all Python scripts.
    ReloadScripts,
    /// Set a breakpoint.
    SetBreakpoint { file: String, line: u32 },
    /// Request the current entity list.
    GetEntityList,
    /// Request properties of a specific entity.
    GetEntityProperties { entity_id: u64 },
    /// Request a frame texture for live preview.
    GetFrameTexture { width: u32, height: u32 },
    /// Toggle debug overlay.
    ToggleDebug(bool),
    /// Request performance stats.
    GetPerformanceStats,
    /// Reload a specific asset.
    ReloadAsset { path: String },
}

/// Messages from the engine to the IDE.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EngineToIde {
    /// Entity list response.
    EntityList(Vec<EntityInfo>),
    /// Entity properties response.
    EntityProperties(EntityPropertiesData),
    /// A rendered frame for live preview.
    FrameTexture {
        width: u32,
        height: u32,
        rgba_data: Vec<u8>,
    },
    /// A script error occurred.
    ScriptError {
        file: String,
        line: u32,
        message: String,
    },
    /// A breakpoint was hit.
    BreakpointHit { file: String, line: u32 },
    /// Game stdout/stderr output.
    GameOutput(String),
    /// Performance stats.
    PerformanceStats {
        fps: f32,
        entity_count: u32,
        draw_calls: u32,
    },
    /// Generic OK acknowledgement.
    Ok,
    /// Error response.
    Error(String),
}

/// Summary info for an entity.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityInfo {
    pub entity_id: u64,
    pub name: String,
    pub node_type: String,
    pub x: f32,
    pub y: f32,
    pub visible: bool,
}

/// Detailed properties for an entity.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityPropertiesData {
    pub entity_id: u64,
    pub name: String,
    pub node_type: String,
    pub x: f32,
    pub y: f32,
    pub rotation: f32,
    pub scale: f32,
    pub visible: bool,
    pub costumes: Vec<String>,
    pub current_costume: usize,
    pub collision_type: String,
    pub physics: Option<PhysicsPropertiesData>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhysicsPropertiesData {
    pub body_type: String,
    pub gravity_scale: f32,
    pub friction: f32,
    pub restitution: f32,
    pub velocity_x: f32,
    pub velocity_y: f32,
}

/// Serialize a message to MessagePack bytes.
pub fn serialize<T: Serialize>(msg: &T) -> Result<Vec<u8>, rmp_serde::encode::Error> {
    rmp_serde::to_vec(msg)
}

/// Deserialize a message from MessagePack bytes.
pub fn deserialize<'a, T: Deserialize<'a>>(data: &'a [u8]) -> Result<T, rmp_serde::decode::Error> {
    rmp_serde::from_slice(data)
}
