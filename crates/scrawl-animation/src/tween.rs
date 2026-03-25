//! Tween system - smooth property interpolation.
//!
//! Supports glide_to, fade, scale, rotate with easing functions.

use bevy::prelude::*;
use scrawl_core::components::Transform2D;

/// Easing function type.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Easing {
    Linear,
    EaseIn,
    EaseOut,
    EaseInOut,
}

impl Easing {
    pub fn apply(&self, t: f32) -> f32 {
        let t = t.clamp(0.0, 1.0);
        match self {
            Easing::Linear => t,
            Easing::EaseIn => t * t,
            Easing::EaseOut => 1.0 - (1.0 - t) * (1.0 - t),
            Easing::EaseInOut => {
                if t < 0.5 {
                    2.0 * t * t
                } else {
                    1.0 - (-2.0 * t + 2.0).powi(2) / 2.0
                }
            }
        }
    }
}

/// What property the tween controls.
#[derive(Debug, Clone)]
pub enum TweenTarget {
    /// Glide to position (x, y).
    Position { target_x: f32, target_y: f32, start_x: f32, start_y: f32 },
    /// Rotate to angle.
    Rotation { target: f32, start: f32 },
    /// Scale to size.
    Scale { target: f32, start: f32 },
    /// Fade alpha.
    Alpha { target: f32, start: f32 },
}

/// Component that drives a tween animation on an entity.
#[derive(Component)]
pub struct Tween {
    pub target: TweenTarget,
    pub duration_secs: f32,
    pub elapsed: f32,
    pub easing: Easing,
    pub finished: bool,
}

impl Tween {
    pub fn glide_to(x: f32, y: f32, duration_ms: f32, easing: Easing, start_x: f32, start_y: f32) -> Self {
        Self {
            target: TweenTarget::Position {
                target_x: x,
                target_y: y,
                start_x,
                start_y,
            },
            duration_secs: duration_ms / 1000.0,
            elapsed: 0.0,
            easing,
            finished: false,
        }
    }

    pub fn rotate_to(angle: f32, duration_ms: f32, easing: Easing, start: f32) -> Self {
        Self {
            target: TweenTarget::Rotation { target: angle, start },
            duration_secs: duration_ms / 1000.0,
            elapsed: 0.0,
            easing,
            finished: false,
        }
    }

    pub fn scale_to(scale: f32, duration_ms: f32, easing: Easing, start: f32) -> Self {
        Self {
            target: TweenTarget::Scale { target: scale, start },
            duration_secs: duration_ms / 1000.0,
            elapsed: 0.0,
            easing,
            finished: false,
        }
    }
}

/// System: update all active tweens.
pub fn update_tweens(
    time: Res<Time>,
    mut query: Query<(&mut Tween, &mut Transform2D)>,
) {
    let dt = time.delta_secs();

    for (mut tween, mut t2d) in query.iter_mut() {
        if tween.finished {
            continue;
        }

        tween.elapsed += dt;
        let progress = (tween.elapsed / tween.duration_secs).min(1.0);
        let t = tween.easing.apply(progress);

        match &tween.target {
            TweenTarget::Position { target_x, target_y, start_x, start_y } => {
                t2d.position.x = start_x + (target_x - start_x) * t;
                t2d.position.y = start_y + (target_y - start_y) * t;
            }
            TweenTarget::Rotation { target, start } => {
                t2d.rotation_degrees = start + (target - start) * t;
            }
            TweenTarget::Scale { target, start } => {
                let s = start + (target - start) * t;
                t2d.scale = Vec2::splat(s);
            }
            TweenTarget::Alpha { .. } => {
                // TODO: sync to SpriteColor alpha when available
            }
        }

        if progress >= 1.0 {
            tween.finished = true;
        }
    }
}

/// System: remove finished tweens.
pub fn cleanup_finished_tweens(
    mut commands: Commands,
    query: Query<(Entity, &Tween)>,
) {
    for (entity, tween) in query.iter() {
        if tween.finished {
            commands.entity(entity).remove::<Tween>();
        }
    }
}
