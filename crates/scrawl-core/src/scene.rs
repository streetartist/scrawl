//! Scene management systems: transform sync, broadcast processing, cleanup.

use bevy::prelude::*;

use crate::components::{SpeechBubble, Transform2D};
use crate::resources::BroadcastQueue;

/// Syncs Transform2D → Bevy Transform each frame.
///
/// This allows users to work with the simple Transform2D API while
/// Bevy's rendering uses the full 3D Transform internally.
pub fn sync_transform2d_to_bevy(
    mut query: Query<(&Transform2D, &mut Transform), Changed<Transform2D>>,
) {
    for (t2d, mut transform) in query.iter_mut() {
        transform.translation.x = t2d.position.x;
        transform.translation.y = t2d.position.y;
        // Convert Scratch-style degrees (0=up, 90=right) to Bevy radians (0=right, CCW)
        let bevy_radians = -(t2d.rotation_degrees - 90.0).to_radians();
        transform.rotation = Quat::from_rotation_z(bevy_radians);
        transform.scale = Vec3::new(t2d.scale.x, t2d.scale.y, 1.0);
    }
}

/// Syncs Bevy Transform → Transform2D (for physics-driven entities).
pub fn sync_bevy_to_transform2d(
    mut query: Query<(&mut Transform2D, &Transform), Changed<Transform>>,
) {
    for (mut t2d, transform) in query.iter_mut() {
        t2d.position.x = transform.translation.x;
        t2d.position.y = transform.translation.y;
        let (_, _, z) = transform.rotation.to_euler(EulerRot::XYZ);
        t2d.rotation_degrees = 90.0 - z.to_degrees();
        t2d.scale.x = transform.scale.x;
        t2d.scale.y = transform.scale.y;
    }
}

/// Clears the broadcast queue at the end of each frame.
pub fn process_broadcast_queue(mut queue: ResMut<BroadcastQueue>) {
    queue.current_frame.clear();
}

/// Decrements speech bubble timers and removes expired ones.
pub fn cleanup_speech_bubbles(
    mut commands: Commands,
    mut query: Query<(Entity, &mut SpeechBubble)>,
    time: Res<Time>,
) {
    for (entity, mut bubble) in query.iter_mut() {
        if let Some(ref mut remaining) = bubble.remaining_secs {
            *remaining -= time.delta_secs();
            if *remaining <= 0.0 {
                commands.entity(entity).remove::<SpeechBubble>();
            }
        }
    }
}
