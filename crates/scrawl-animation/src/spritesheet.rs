//! Sprite sheet animation system.
//!
//! Automatically cycles through frames of a sprite sheet atlas at a given FPS.

use bevy::prelude::*;
use scrawl_core::components::CostumeSet;

/// Component that drives automatic sprite sheet animation.
#[derive(Component)]
pub struct SpriteSheetAnimation {
    /// Frames per second for the animation.
    pub fps: f32,
    /// Whether to loop when reaching the last frame.
    pub looping: bool,
    /// Whether the animation is currently playing.
    pub playing: bool,
    /// Accumulated time since last frame change.
    pub timer: f32,
    /// First frame index (inclusive).
    pub start_frame: usize,
    /// Last frame index (inclusive).
    pub end_frame: usize,
}

impl Default for SpriteSheetAnimation {
    fn default() -> Self {
        Self {
            fps: 12.0,
            looping: true,
            playing: true,
            timer: 0.0,
            start_frame: 0,
            end_frame: 0,
        }
    }
}

impl SpriteSheetAnimation {
    pub fn new(start: usize, end: usize, fps: f32) -> Self {
        Self {
            fps,
            start_frame: start,
            end_frame: end,
            ..Default::default()
        }
    }

    pub fn play(&mut self) {
        self.playing = true;
    }

    pub fn stop(&mut self) {
        self.playing = false;
    }

    pub fn reset(&mut self) {
        self.timer = 0.0;
    }
}

/// System: advance sprite sheet animations each frame.
pub fn animate_spritesheets(
    time: Res<Time>,
    mut query: Query<(&mut SpriteSheetAnimation, &mut CostumeSet)>,
) {
    let dt = time.delta_secs();

    for (mut anim, mut costumes) in query.iter_mut() {
        if !anim.playing || anim.fps <= 0.0 || costumes.costumes.is_empty() {
            continue;
        }

        anim.timer += dt;
        let frame_duration = 1.0 / anim.fps;

        if anim.timer >= frame_duration {
            anim.timer -= frame_duration;

            let next = costumes.current + 1;
            if next > anim.end_frame {
                if anim.looping {
                    costumes.current = anim.start_frame;
                } else {
                    anim.playing = false;
                }
            } else {
                costumes.current = next;
            }
        }
    }
}
