//! Core resources for the Scrawl engine.

use bevy::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use crate::events::InputMode;

/// Global engine configuration.
#[derive(Resource, Debug, Clone, Serialize, Deserialize)]
pub struct ScrawlConfig {
    pub width: u32,
    pub height: u32,
    pub title: String,
    pub fps: u32,
    pub fullscreen: bool,
    pub debug: bool,
}

impl Default for ScrawlConfig {
    fn default() -> Self {
        Self {
            width: 800,
            height: 600,
            title: "Scrawl Game".to_string(),
            fps: 60,
            fullscreen: false,
            debug: false,
        }
    }
}

/// Tracks broadcast messages for the current frame.
#[derive(Resource, Debug, Default)]
pub struct BroadcastQueue {
    /// Broadcasts fired this frame (cleared each frame in PostUpdate).
    pub current_frame: HashSet<String>,
    /// History of all broadcasts with timestamps.
    pub history: HashMap<String, f64>,
}

/// Current mouse state.
#[derive(Resource, Debug, Default)]
pub struct MouseState {
    pub position: Vec2,
    pub pressed: bool,
    pub just_pressed: bool,
    pub just_released: bool,
}

/// Tracks which keys are currently held.
#[derive(Resource, Debug, Default)]
pub struct KeyState {
    pub held_keys: HashSet<KeyCode>,
}

/// Buffered input events. Written in Update, consumed in FixedUpdate.
#[derive(Resource, Debug, Default)]
pub struct InputBuffer {
    pub key_events: Vec<(KeyCode, InputMode)>,
    pub mouse_events: Vec<(MouseButton, InputMode, Vec2)>,
}

/// Manages scenes: active scene and scene registry.
#[derive(Resource, Debug, Default)]
pub struct SceneManager {
    /// Entity of the currently active scene root.
    pub active_scene: Option<Entity>,
    /// Map of scene name -> serialized scene data for switching.
    pub scene_registry: HashMap<String, SceneData>,
}

/// Serialized scene data for scene switching.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SceneData {
    pub name: String,
    pub background_color: [f32; 4],
    pub background_image: Option<String>,
    pub sprites: Vec<SpriteData>,
}

/// Serialized sprite data.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpriteData {
    pub name: String,
    pub class_name: String,
    pub x: f32,
    pub y: f32,
    pub direction: f32,
    pub size: f32,
    pub visible: bool,
    pub costumes: Vec<CostumeData>,
    pub collision_type: String,
    pub physics: Option<PhysicsSpriteData>,
    pub code: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostumeData {
    pub name: String,
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhysicsSpriteData {
    pub gravity_scale: f32,
    pub friction: f32,
    pub restitution: f32,
    pub body_type: String,
}
