//! Scrawl Animation - Sprite sheet animation, tweening, and property animation.

pub mod spritesheet;
pub mod tween;

use bevy::prelude::*;
use scrawl_core::schedule::ScrawlSet;

/// Animation plugin - handles sprite sheet playback and tween interpolation.
pub struct ScrawlAnimationPlugin;

impl Plugin for ScrawlAnimationPlugin {
    fn build(&self, app: &mut App) {
        app.add_systems(
            FixedUpdate,
            (
                spritesheet::animate_spritesheets,
                tween::update_tweens,
                tween::cleanup_finished_tweens,
            )
                .in_set(ScrawlSet::Animation),
        );
    }
}
