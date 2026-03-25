//! ScriptContext - the API surface available to scripts for interacting with the ECS.
//!
//! Both Python and Rust scripts interact with the game world through ScriptContext.
//! It provides a Scratch-like API (move, turn, say, clone, etc.) that internally
//! manipulates ECS components.

use bevy::prelude::*;
use scrawl_core::components::*;
use scrawl_core::events::BroadcastEvent;

/// Context passed to script callbacks, providing the game API.
///
/// This is a short-lived reference that borrows the ECS World for the
/// duration of a script callback. It operates on a specific entity.
pub struct ScriptContext<'w> {
    pub entity: Entity,
    pub world: &'w mut World,
}

impl<'w> ScriptContext<'w> {
    pub fn new(entity: Entity, world: &'w mut World) -> Self {
        Self { entity, world }
    }

    // ========================================================================
    // Transform
    // ========================================================================

    /// Move in the current direction by `steps` pixels.
    pub fn move_steps(&mut self, steps: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.move_steps(steps);
        }
    }

    /// Turn left (counterclockwise) by degrees.
    pub fn turn_left(&mut self, degrees: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.turn_left(degrees);
        }
    }

    /// Turn right (clockwise) by degrees.
    pub fn turn_right(&mut self, degrees: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.turn_right(degrees);
        }
    }

    /// Go to a specific position.
    pub fn go_to(&mut self, x: f32, y: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.position = Vec2::new(x, y);
        }
    }

    /// Set the X position.
    pub fn set_x(&mut self, x: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.position.x = x;
        }
    }

    /// Set the Y position.
    pub fn set_y(&mut self, y: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.position.y = y;
        }
    }

    /// Change X by a delta.
    pub fn change_x(&mut self, dx: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.position.x += dx;
        }
    }

    /// Change Y by a delta.
    pub fn change_y(&mut self, dy: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.position.y += dy;
        }
    }

    /// Get current position.
    pub fn position(&self) -> Vec2 {
        self.world
            .get::<Transform2D>(self.entity)
            .map(|t| t.position)
            .unwrap_or(Vec2::ZERO)
    }

    /// Get current direction in degrees.
    pub fn direction(&self) -> f32 {
        self.world
            .get::<Transform2D>(self.entity)
            .map(|t| t.rotation_degrees)
            .unwrap_or(90.0)
    }

    /// Set direction in degrees.
    pub fn set_direction(&mut self, degrees: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.rotation_degrees = degrees;
        }
    }

    /// Point towards a position.
    pub fn point_towards(&mut self, x: f32, y: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.point_towards(Vec2::new(x, y));
        }
    }

    // ========================================================================
    // Appearance
    // ========================================================================

    /// Set the current costume by name.
    pub fn set_costume(&mut self, name: &str) {
        if let Some(mut costumes) = self.world.get_mut::<CostumeSet>(self.entity) {
            costumes.switch_to(name);
        }
    }

    /// Switch to the next costume.
    pub fn next_costume(&mut self) {
        if let Some(mut costumes) = self.world.get_mut::<CostumeSet>(self.entity) {
            costumes.next_costume();
        }
    }

    /// Set visibility.
    pub fn set_visible(&mut self, visible: bool) {
        if let Some(mut v) = self.world.get_mut::<Visible>(self.entity) {
            v.0 = visible;
        }
    }

    /// Show the sprite.
    pub fn show(&mut self) {
        self.set_visible(true);
    }

    /// Hide the sprite.
    pub fn hide(&mut self) {
        self.set_visible(false);
    }

    /// Set the size scale.
    pub fn set_size(&mut self, scale: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.scale = Vec2::splat(scale);
        }
    }

    /// Change size by a delta.
    pub fn change_size(&mut self, delta: f32) {
        if let Some(mut t2d) = self.world.get_mut::<Transform2D>(self.entity) {
            t2d.scale += Vec2::splat(delta);
        }
    }

    /// Set the sprite tint color.
    pub fn set_color(&mut self, r: f32, g: f32, b: f32) {
        if let Some(mut color) = self.world.get_mut::<SpriteColor>(self.entity) {
            color.0 = Color::srgb(r, g, b);
        }
    }

    // ========================================================================
    // Speech
    // ========================================================================

    /// Display a speech bubble.
    pub fn say(&mut self, text: &str, duration_ms: u32) {
        let secs = if duration_ms == 0 {
            None
        } else {
            Some(duration_ms as f32 / 1000.0)
        };
        self.world.entity_mut(self.entity).insert(SpeechBubble {
            text: text.to_string(),
            remaining_secs: secs,
            is_thought: false,
        });
    }

    /// Display a thought bubble.
    pub fn think(&mut self, text: &str, duration_ms: u32) {
        let secs = if duration_ms == 0 {
            None
        } else {
            Some(duration_ms as f32 / 1000.0)
        };
        self.world.entity_mut(self.entity).insert(SpeechBubble {
            text: text.to_string(),
            remaining_secs: secs,
            is_thought: true,
        });
    }

    // ========================================================================
    // Pen
    // ========================================================================

    /// Put the pen down (start drawing).
    pub fn pen_down(&mut self) {
        if let Some(mut pen) = self.world.get_mut::<PenState>(self.entity) {
            pen.down = true;
        }
    }

    /// Lift the pen up (stop drawing).
    pub fn pen_up(&mut self) {
        if let Some(mut pen) = self.world.get_mut::<PenState>(self.entity) {
            pen.down = false;
        }
    }

    /// Clear all pen drawings for this sprite.
    pub fn pen_clear(&mut self) {
        if let Some(mut pen) = self.world.get_mut::<PenState>(self.entity) {
            pen.path.clear();
        }
    }

    /// Set pen color.
    pub fn set_pen_color(&mut self, r: f32, g: f32, b: f32) {
        if let Some(mut pen) = self.world.get_mut::<PenState>(self.entity) {
            pen.color = Color::srgb(r, g, b);
        }
    }

    /// Set pen size.
    pub fn set_pen_size(&mut self, size: f32) {
        if let Some(mut pen) = self.world.get_mut::<PenState>(self.entity) {
            pen.size = size;
        }
    }

    // ========================================================================
    // Events
    // ========================================================================

    /// Send a broadcast message to all sprites.
    pub fn broadcast(&mut self, event: &str) {
        self.world.send_event(BroadcastEvent(event.to_string()));
    }

    // ========================================================================
    // Clone
    // ========================================================================

    /// Clone this sprite. The clone will have IsClone component.
    pub fn clone_self(&mut self) {
        // Read all components from the original entity
        let t2d = self.world.get::<Transform2D>(self.entity).cloned();
        let costume_set = self.world.get::<CostumeSet>(self.entity).cloned();
        let sprite_color = self.world.get::<SpriteColor>(self.entity).cloned();
        let visible = self.world.get::<Visible>(self.entity).cloned();
        let collision = self.world.get::<CollisionShape>(self.entity).cloned();
        let name = self.world.get::<ScrawlName>(self.entity).cloned();
        let pen = self.world.get::<PenState>(self.entity).cloned();

        let mut clone = self.world.spawn((
            ScrawlId::default(),
            IsClone,
            Transform::default(),
        ));

        if let Some(t) = t2d {
            clone.insert(t);
        }
        if let Some(c) = costume_set {
            clone.insert(c);
        }
        if let Some(c) = sprite_color {
            clone.insert(c);
        }
        if let Some(v) = visible {
            clone.insert(v);
        }
        if let Some(c) = collision {
            clone.insert(c);
        }
        if let Some(n) = name {
            clone.insert(ScrawlName(format!("{}_clone", n.0)));
        }
        if let Some(p) = pen {
            clone.insert(PenState {
                path: Vec::new(),
                ..p
            });
        }
    }

    /// Delete this entity.
    pub fn delete_self(&mut self) {
        self.world.despawn(self.entity);
    }

    // ========================================================================
    // Physics (basic)
    // ========================================================================

    /// Set velocity (for PhysicsSprite).
    pub fn set_velocity(&mut self, vx: f32, vy: f32) {
        if let Some(mut vel) = self.world.get_mut::<Velocity2D>(self.entity) {
            vel.linear = Vec2::new(vx, vy);
        }
    }

    /// Get velocity.
    pub fn velocity(&self) -> Vec2 {
        self.world
            .get::<Velocity2D>(self.entity)
            .map(|v| v.linear)
            .unwrap_or(Vec2::ZERO)
    }

    // ========================================================================
    // Query helpers
    // ========================================================================

    /// Get the entity's name.
    pub fn name(&self) -> String {
        self.world
            .get::<ScrawlName>(self.entity)
            .map(|n| n.0.clone())
            .unwrap_or_default()
    }

    /// Set the entity's name.
    pub fn set_name(&mut self, name: &str) {
        if let Some(mut n) = self.world.get_mut::<ScrawlName>(self.entity) {
            n.0 = name.to_string();
        }
    }
}
