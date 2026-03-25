//! Core ECS components for the Scrawl engine.

use bevy::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ============================================================================
// Identity
// ============================================================================

/// Human-readable name for an entity (e.g., "Ball", "Player").
#[derive(Component, Debug, Clone, Serialize, Deserialize)]
pub struct ScrawlName(pub String);

/// Unique persistent ID for an entity (survives save/load).
#[derive(Component, Debug, Clone, Serialize, Deserialize)]
pub struct ScrawlId(pub Uuid);

impl Default for ScrawlId {
    fn default() -> Self {
        Self(Uuid::new_v4())
    }
}

// ============================================================================
// Scene Tree
// ============================================================================

/// Marks the root entity of a scene.
#[derive(Component, Debug, Default)]
pub struct SceneRoot;

/// The type of node in the scene tree.
#[derive(Component, Debug, Clone, Serialize, Deserialize)]
pub struct NodeType(pub NodeKind);

/// All possible node kinds in the Scrawl engine.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum NodeKind {
    Sprite,
    PhysicsBody,
    TileMap,
    ParticleEmitter,
    AudioSource,
    UINode,
    Camera,
    Empty,
}

impl Default for NodeType {
    fn default() -> Self {
        Self(NodeKind::Sprite)
    }
}

// ============================================================================
// Transform2D (convenience wrapper, syncs with Bevy Transform)
// ============================================================================

/// 2D transform component that syncs with Bevy's Transform.
///
/// Uses Scratch-style rotation where 90° = pointing right.
/// The sync system converts between this and Bevy's Transform each frame.
/// This keeps the 2D API simple while the 3D-ready Transform handles rendering.
#[derive(Component, Debug, Clone, Serialize, Deserialize)]
pub struct Transform2D {
    /// Position in 2D world space.
    pub position: Vec2,
    /// Rotation in degrees (Scratch-style: 0=up, 90=right, 180=down, 270=left).
    pub rotation_degrees: f32,
    /// Scale factor (uniform by default, Vec2 for non-uniform).
    pub scale: Vec2,
}

impl Default for Transform2D {
    fn default() -> Self {
        Self {
            position: Vec2::ZERO,
            rotation_degrees: 90.0, // Facing right (Scratch default)
            scale: Vec2::ONE,
        }
    }
}

impl Transform2D {
    pub fn new(x: f32, y: f32) -> Self {
        Self {
            position: Vec2::new(x, y),
            ..Default::default()
        }
    }

    /// Direction as a unit vector (based on rotation_degrees).
    pub fn direction_vector(&self) -> Vec2 {
        let rad = (self.rotation_degrees - 90.0).to_radians();
        Vec2::new(rad.cos(), -rad.sin())
    }

    /// Move in the current direction by `steps` pixels.
    pub fn move_steps(&mut self, steps: f32) {
        let dir = self.direction_vector();
        self.position += dir * steps;
    }

    /// Turn left (counterclockwise) by degrees.
    pub fn turn_left(&mut self, degrees: f32) {
        self.rotation_degrees -= degrees;
    }

    /// Turn right (clockwise) by degrees.
    pub fn turn_right(&mut self, degrees: f32) {
        self.rotation_degrees += degrees;
    }

    /// Point towards a position.
    pub fn point_towards(&mut self, target: Vec2) {
        let delta = target - self.position;
        self.rotation_degrees = delta.y.atan2(delta.x).to_degrees() + 90.0;
    }
}

// ============================================================================
// Sprite Rendering
// ============================================================================

/// A single costume (image) entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostumeEntry {
    pub name: String,
    /// Asset path or handle. At runtime, `handle` is used.
    pub path: String,
    #[serde(skip)]
    pub handle: Option<Handle<Image>>,
}

/// Collection of costumes for a sprite, with the current costume index.
#[derive(Component, Debug, Clone, Default, Serialize, Deserialize)]
pub struct CostumeSet {
    pub costumes: Vec<CostumeEntry>,
    pub current: usize,
}

impl CostumeSet {
    pub fn current_costume(&self) -> Option<&CostumeEntry> {
        self.costumes.get(self.current)
    }

    pub fn switch_to(&mut self, name: &str) -> bool {
        if let Some(idx) = self.costumes.iter().position(|c| c.name == name) {
            self.current = idx;
            true
        } else {
            false
        }
    }

    pub fn next_costume(&mut self) {
        if !self.costumes.is_empty() {
            self.current = (self.current + 1) % self.costumes.len();
        }
    }
}

/// Tint color for the sprite.
#[derive(Component, Debug, Clone, Serialize, Deserialize)]
pub struct SpriteColor(pub Color);

impl Default for SpriteColor {
    fn default() -> Self {
        Self(Color::WHITE)
    }
}

/// Whether the entity is visible.
#[derive(Component, Debug, Clone, Serialize, Deserialize)]
pub struct Visible(pub bool);

impl Default for Visible {
    fn default() -> Self {
        Self(true)
    }
}

/// Layer ordering for rendering (higher = drawn on top).
#[derive(Component, Debug, Clone, Default, Serialize, Deserialize)]
pub struct DrawOrder(pub i32);

// ============================================================================
// Pen Drawing
// ============================================================================

/// Pen drawing state for a sprite (like Scratch's pen).
#[derive(Component, Debug, Clone, Serialize, Deserialize)]
pub struct PenState {
    pub down: bool,
    pub color: Color,
    pub size: f32,
    #[serde(skip)]
    pub path: Vec<Vec2>,
}

impl Default for PenState {
    fn default() -> Self {
        Self {
            down: false,
            color: Color::BLACK,
            size: 2.0,
            path: Vec::new(),
        }
    }
}

// ============================================================================
// Speech Bubble
// ============================================================================

/// A speech/thought bubble above a sprite.
#[derive(Component, Debug, Clone)]
pub struct SpeechBubble {
    pub text: String,
    /// Remaining time in seconds. None = permanent until cleared.
    pub remaining_secs: Option<f32>,
    pub is_thought: bool,
}

// ============================================================================
// Collision
// ============================================================================

/// The collision detection mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CollisionKind {
    /// Axis-aligned bounding box.
    Rect,
    /// Circle with radius.
    Circle,
    /// Pixel-perfect mask (expensive).
    Mask,
}

/// Collision shape component.
#[derive(Component, Debug, Clone, Serialize, Deserialize)]
pub struct CollisionShape {
    pub kind: CollisionKind,
    /// Radius for Circle mode (auto-calculated from sprite size if not set).
    pub radius: Option<f32>,
}

impl Default for CollisionShape {
    fn default() -> Self {
        Self {
            kind: CollisionKind::Rect,
            radius: None,
        }
    }
}

/// Pixel-perfect collision bitmask, generated from sprite image alpha channel.
///
/// Each bit represents one pixel: 1 = solid (alpha > threshold), 0 = transparent.
/// The mask is stored row-major, with `width` pixels per row.
#[derive(Component, Debug, Clone)]
pub struct CollisionMask {
    pub width: u32,
    pub height: u32,
    /// Packed bits: bit index = y * width + x
    pub bits: Vec<u32>,
}

impl CollisionMask {
    /// Create a mask from RGBA image data.
    /// Pixels with alpha > `alpha_threshold` are considered solid.
    pub fn from_rgba(data: &[u8], width: u32, height: u32, alpha_threshold: u8) -> Self {
        let total_pixels = (width * height) as usize;
        let num_words = (total_pixels + 31) / 32;
        let mut bits = vec![0u32; num_words];

        for i in 0..total_pixels {
            let alpha = data[i * 4 + 3];
            if alpha > alpha_threshold {
                bits[i / 32] |= 1 << (i % 32);
            }
        }

        Self { width, height, bits }
    }

    /// Check if a pixel is solid.
    pub fn is_solid(&self, x: i32, y: i32) -> bool {
        if x < 0 || y < 0 || x >= self.width as i32 || y >= self.height as i32 {
            return false;
        }
        let idx = (y as u32 * self.width + x as u32) as usize;
        (self.bits[idx / 32] >> (idx % 32)) & 1 == 1
    }

    /// Check if two masks overlap given their world positions and scales.
    /// Returns true if any solid pixels overlap.
    pub fn overlaps(
        &self,
        pos_a: Vec2,
        scale_a: Vec2,
        other: &CollisionMask,
        pos_b: Vec2,
        scale_b: Vec2,
    ) -> bool {
        // Compute world-space bounding boxes
        let a_size = Vec2::new(self.width as f32 * scale_a.x, self.height as f32 * scale_a.y);
        let b_size = Vec2::new(other.width as f32 * scale_b.x, other.height as f32 * scale_b.y);

        let a_min = pos_a - a_size / 2.0;
        let a_max = pos_a + a_size / 2.0;
        let b_min = pos_b - b_size / 2.0;
        let b_max = pos_b + b_size / 2.0;

        // AABB early exit
        if a_max.x <= b_min.x || a_min.x >= b_max.x || a_max.y <= b_min.y || a_min.y >= b_max.y {
            return false;
        }

        // Overlap region in world space
        let overlap_min = Vec2::new(a_min.x.max(b_min.x), a_min.y.max(b_min.y));
        let overlap_max = Vec2::new(a_max.x.min(b_max.x), a_max.y.min(b_max.y));

        // Sample at the smaller scale's resolution for accuracy
        let step = scale_a.x.min(scale_b.x).min(scale_a.y).min(scale_b.y).max(0.5);

        let mut wy = overlap_min.y;
        while wy < overlap_max.y {
            let mut wx = overlap_min.x;
            while wx < overlap_max.x {
                // Convert world position to each mask's pixel coords
                let ax = ((wx - a_min.x) / scale_a.x) as i32;
                let ay = ((wy - a_min.y) / scale_a.y) as i32;
                let bx = ((wx - b_min.x) / scale_b.x) as i32;
                let by = ((wy - b_min.y) / scale_b.y) as i32;

                if self.is_solid(ax, ay) && other.is_solid(bx, by) {
                    return true;
                }
                wx += step;
            }
            wy += step;
        }

        false
    }
}

// ============================================================================
// Script Binding Markers
// ============================================================================

/// Marks an entity as bound to a Python script instance.
#[derive(Component, Debug)]
pub struct PythonScriptRef {
    pub class_name: String,
    pub instance_id: u64,
}

/// Marks an entity as a clone (created via sprite.clone()).
#[derive(Component, Debug, Default)]
pub struct IsClone;

// ============================================================================
// Physics (basic, for use without Rapier - compatibility with v1 PhysicsSprite)
// ============================================================================

/// Simple velocity component (used by basic physics and synced to Rapier when available).
#[derive(Component, Debug, Clone, Default, Serialize, Deserialize)]
pub struct Velocity2D {
    pub linear: Vec2,
    pub angular: f32,
}

/// Basic physics properties.
#[derive(Component, Debug, Clone, Serialize, Deserialize)]
pub struct PhysicsProps {
    pub gravity_scale: f32,
    pub friction: f32,
    pub restitution: f32,
    pub body_type: PhysicsBodyType,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PhysicsBodyType {
    Dynamic,
    Static,
    Kinematic,
}

impl Default for PhysicsProps {
    fn default() -> Self {
        Self {
            gravity_scale: 1.0,
            friction: 0.02,
            restitution: 0.8,
            body_type: PhysicsBodyType::Dynamic,
        }
    }
}
