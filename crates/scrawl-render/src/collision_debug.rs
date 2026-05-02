//! Debug collision visualization.
//! Draws wireframe shapes for visible sprites. Hidden sprites are skipped.
//! Colors: Green=Rect, Cyan=Circle, Orange=Mask(active), Red=Mask(loading)

use bevy::prelude::*;
use scrawl_core::components::{CollisionKind, CollisionMask, CollisionShape, ScrawlName, Transform2D, Visible};
use scrawl_core::resources::ScrawlConfig;

pub fn draw_collision_debug(
    config: Res<ScrawlConfig>,
    mut gizmos: Gizmos,
    images: Res<Assets<Image>>,
    query: Query<(&Transform2D, &CollisionShape, &Visible, &Sprite, Option<&CollisionMask>, Option<&ScrawlName>)>,
) {
    if !config.debug {
        return;
    }

    for (t2d, shape, vis, sprite, mask, _name) in query.iter() {
        if !vis.0 {
            continue;
        }

        let pos = t2d.position;
        let angle = -(t2d.rotation_degrees - 90.0).to_radians();
        let rotation = Rot2::radians(angle);
        let isometry = Isometry2d::new(pos, rotation);
        let base_size = get_sprite_size(sprite, &images);
        let scaled = base_size * t2d.scale;

        match shape.kind {
            CollisionKind::Rect => {
                gizmos.rect_2d(isometry, scaled, Color::srgba(0.0, 1.0, 0.0, 0.6));
            }
            CollisionKind::Circle => {
                let radius = shape.radius.unwrap_or(scaled.x.max(scaled.y) / 2.0);
                gizmos.circle_2d(
                    Isometry2d::from_translation(pos),
                    radius,
                    Color::srgba(0.0, 0.8, 1.0, 0.6),
                );
            }
            CollisionKind::Mask => {
                if mask.is_some() {
                    // Mask active: orange outline + inner cross to distinguish from rect
                    let color = Color::srgba(1.0, 0.5, 0.0, 0.6);
                    gizmos.rect_2d(isometry, scaled, color);
                    // Draw an X inside to visually distinguish mask from rect
                    let half = scaled / 2.0;
                    let corners = [
                        Vec2::new(-half.x, -half.y),
                        Vec2::new(half.x, half.y),
                        Vec2::new(-half.x, half.y),
                        Vec2::new(half.x, -half.y),
                    ];
                    let cos = angle.cos();
                    let sin = angle.sin();
                    let rotate = |v: Vec2| Vec2::new(v.x * cos - v.y * sin, v.x * sin + v.y * cos) + pos;
                    gizmos.line_2d(rotate(corners[0]), rotate(corners[1]), color);
                    gizmos.line_2d(rotate(corners[2]), rotate(corners[3]), color);
                } else {
                    // Mask not yet generated: red dashed outline
                    gizmos.rect_2d(isometry, scaled, Color::srgba(1.0, 0.0, 0.0, 0.4));
                }
            }
        }
    }
}

fn get_sprite_size(sprite: &Sprite, images: &Assets<Image>) -> Vec2 {
    if let Some(size) = sprite.custom_size {
        return size;
    }
    if let Some(image) = images.get(&sprite.image) {
        Vec2::new(image.width() as f32, image.height() as f32)
    } else {
        Vec2::new(50.0, 50.0)
    }
}
