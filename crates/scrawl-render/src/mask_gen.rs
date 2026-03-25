//! Auto-generate CollisionMask from sprite images when collision_type is "mask".

use bevy::prelude::*;
use scrawl_core::components::{CollisionKind, CollisionMask, CollisionShape, CostumeSet};

/// System: when an entity has CollisionKind::Mask and a loaded image,
/// generate the CollisionMask from the image's alpha channel.
pub fn generate_collision_masks(
    mut commands: Commands,
    images: Res<Assets<Image>>,
    query: Query<
        (Entity, &CollisionShape, &CostumeSet),
        (Without<CollisionMask>,),
    >,
) {
    for (entity, shape, costumes) in query.iter() {
        if shape.kind != CollisionKind::Mask {
            continue;
        }

        // Get the current costume's image handle
        let handle = costumes
            .current_costume()
            .and_then(|c| c.handle.as_ref());

        if let Some(handle) = handle {
            if let Some(image) = images.get(handle) {
                // Generate mask from image RGBA data
                let width = image.width();
                let height = image.height();
                let data = &image.data;

                // Check if RGBA format (4 bytes per pixel)
                if data.len() >= (width * height * 4) as usize {
                    let mask = CollisionMask::from_rgba(data, width, height, 10);
                    commands.entity(entity).insert(mask);
                    log::info!(
                        "Generated collision mask for entity {:?}: {}x{}",
                        entity, width, height
                    );
                }
            }
        }
    }
}
