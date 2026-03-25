//! Collision detection systems.
//!
//! Supports rect (OBB), circle, and mixed rect-circle collisions.
//! All collision shapes follow the entity's Transform2D (position, rotation, scale).

use bevy::prelude::*;

use crate::components::{CollisionKind, CollisionMask, CollisionShape, Transform2D, Visible};
use crate::events::{Edge, EdgeCollisionEvent, SpriteCollisionEvent};
use crate::resources::ScrawlConfig;

/// System: detect sprites touching screen edges.
/// Uses design resolution (ScrawlConfig) — the camera letterbox keeps
/// the game coordinate system fixed regardless of window/fullscreen size.
pub fn detect_edge_collisions(
    config: Res<ScrawlConfig>,
    query: Query<(Entity, &Transform2D, &CollisionShape, Option<&Sprite>, Option<&CollisionMask>)>,
    mut edge_events: EventWriter<EdgeCollisionEvent>,
) {
    let w = config.width as f32;
    let h = config.height as f32;

    for (entity, t2d, shape, sprite, mask) in query.iter() {
        let pos = t2d.position;

        match shape.kind {
            CollisionKind::Circle => {
                let r = get_circle_radius(t2d, shape, sprite, mask);
                if pos.x - r <= 0.0 {
                    edge_events.send(EdgeCollisionEvent { entity, edge: Edge::Left });
                }
                if pos.x + r >= w {
                    edge_events.send(EdgeCollisionEvent { entity, edge: Edge::Right });
                }
                if pos.y + r >= h {
                    edge_events.send(EdgeCollisionEvent { entity, edge: Edge::Top });
                }
                if pos.y - r <= 0.0 {
                    edge_events.send(EdgeCollisionEvent { entity, edge: Edge::Bottom });
                }
            }
            _ => {
                // Rect / Mask: use AABB of rotated rect
                let half = get_half_size(t2d, sprite, mask);
                let aabb_half = rotated_aabb_half(half, t2d.rotation_degrees);
                if pos.x - aabb_half.x <= 0.0 {
                    edge_events.send(EdgeCollisionEvent { entity, edge: Edge::Left });
                }
                if pos.x + aabb_half.x >= w {
                    edge_events.send(EdgeCollisionEvent { entity, edge: Edge::Right });
                }
                if pos.y + aabb_half.y >= h {
                    edge_events.send(EdgeCollisionEvent { entity, edge: Edge::Top });
                }
                if pos.y - aabb_half.y <= 0.0 {
                    edge_events.send(EdgeCollisionEvent { entity, edge: Edge::Bottom });
                }
            }
        }
    }
}

/// System: detect sprite-to-sprite collisions.
pub fn detect_sprite_collisions(
    query: Query<(Entity, &Transform2D, &CollisionShape, Option<&Sprite>, &Visible, Option<&CollisionMask>)>,
    mut collision_events: EventWriter<SpriteCollisionEvent>,
) {
    let entities: Vec<_> = query.iter().filter(|(_, _, _, _, vis, _)| vis.0).collect();

    for i in 0..entities.len() {
        for j in (i + 1)..entities.len() {
            let (ea, ta, sa, spa, _, ma) = &entities[i];
            let (eb, tb, sb, spb, _, mb) = &entities[j];

            let colliding = match (&sa.kind, &sb.kind) {
                (CollisionKind::Circle, CollisionKind::Circle) => {
                    circle_vs_circle(ta, sa, *spa, *ma, tb, sb, *spb, *mb)
                }
                (CollisionKind::Rect, CollisionKind::Rect) => {
                    obb_vs_obb(ta, *spa, *ma, tb, *spb, *mb)
                }
                (CollisionKind::Mask, CollisionKind::Mask) => {
                    if let (Some(mask_a), Some(mask_b)) = (ma, mb) {
                        mask_a.overlaps(ta.position, ta.scale, mask_b, tb.position, tb.scale)
                    } else {
                        obb_vs_obb(ta, *spa, *ma, tb, *spb, *mb)
                    }
                }
                (CollisionKind::Mask, CollisionKind::Rect) | (CollisionKind::Rect, CollisionKind::Mask) => {
                    obb_vs_obb(ta, *spa, *ma, tb, *spb, *mb)
                }
                (CollisionKind::Circle, _) => {
                    circle_vs_obb(ta, sa, *spa, *ma, tb, *spb, *mb)
                }
                (_, CollisionKind::Circle) => {
                    circle_vs_obb(tb, sb, *spb, *mb, ta, *spa, *ma)
                }
            };

            if colliding {
                collision_events.send(SpriteCollisionEvent {
                    entity_a: *ea,
                    entity_b: *eb,
                });
            }
        }
    }
}

// ============================================================================
// Helpers
// ============================================================================

fn get_half_size(t2d: &Transform2D, sprite: Option<&Sprite>, mask: Option<&CollisionMask>) -> Vec2 {
    // Try custom_size first, then mask dimensions, then default
    let base = sprite
        .and_then(|s| s.custom_size)
        .or_else(|| mask.map(|m| Vec2::new(m.width as f32, m.height as f32)))
        .unwrap_or(Vec2::new(50.0, 50.0));
    base * t2d.scale / 2.0
}

fn get_circle_radius(t2d: &Transform2D, shape: &CollisionShape, sprite: Option<&Sprite>, mask: Option<&CollisionMask>) -> f32 {
    if let Some(r) = shape.radius {
        r * t2d.scale.x
    } else {
        let half = get_half_size(t2d, sprite, mask);
        half.x.max(half.y)
    }
}

/// Compute AABB half-extents of a rotated rectangle.
fn rotated_aabb_half(half: Vec2, rotation_degrees: f32) -> Vec2 {
    let rad = (rotation_degrees - 90.0).to_radians();
    let cos = rad.cos().abs();
    let sin = rad.sin().abs();
    Vec2::new(
        half.x * cos + half.y * sin,
        half.x * sin + half.y * cos,
    )
}

/// Get the two local axes of an OBB from rotation degrees.
fn obb_axes(rotation_degrees: f32) -> [Vec2; 2] {
    let rad = (rotation_degrees - 90.0).to_radians();
    let cos = rad.cos();
    let sin = rad.sin();
    [Vec2::new(cos, -sin), Vec2::new(sin, cos)]
}

/// Circle vs Circle.
fn circle_vs_circle(
    ta: &Transform2D, sa: &CollisionShape, spa: Option<&Sprite>, ma: Option<&CollisionMask>,
    tb: &Transform2D, sb: &CollisionShape, spb: Option<&Sprite>, mb: Option<&CollisionMask>,
) -> bool {
    let ra = get_circle_radius(ta, sa, spa, ma);
    let rb = get_circle_radius(tb, sb, spb, mb);
    let dist_sq = ta.position.distance_squared(tb.position);
    dist_sq < (ra + rb) * (ra + rb)
}

/// OBB vs OBB using Separating Axis Theorem (SAT).
fn obb_vs_obb(
    ta: &Transform2D, spa: Option<&Sprite>, ma: Option<&CollisionMask>,
    tb: &Transform2D, spb: Option<&Sprite>, mb: Option<&CollisionMask>,
) -> bool {
    let ha = get_half_size(ta, spa, ma);
    let hb = get_half_size(tb, spb, mb);
    let axes_a = obb_axes(ta.rotation_degrees);
    let axes_b = obb_axes(tb.rotation_degrees);
    let d = tb.position - ta.position;

    // Test 4 axes (2 from each OBB)
    for axis in axes_a.iter().chain(axes_b.iter()) {
        let proj_a = ha.x * axes_a[0].dot(*axis).abs() + ha.y * axes_a[1].dot(*axis).abs();
        let proj_b = hb.x * axes_b[0].dot(*axis).abs() + hb.y * axes_b[1].dot(*axis).abs();
        let dist = d.dot(*axis).abs();

        if dist > proj_a + proj_b {
            return false; // Separating axis found
        }
    }

    true
}

/// Circle vs OBB.
fn circle_vs_obb(
    tc: &Transform2D, sc: &CollisionShape, spc: Option<&Sprite>, mc: Option<&CollisionMask>,
    tr: &Transform2D, spr: Option<&Sprite>, mr: Option<&CollisionMask>,
) -> bool {
    let radius = get_circle_radius(tc, sc, spc, mc);
    let half = get_half_size(tr, spr, mr);
    let axes = obb_axes(tr.rotation_degrees);

    // Transform circle center into OBB's local space
    let d = tc.position - tr.position;
    let local_x = d.dot(axes[0]);
    let local_y = d.dot(axes[1]);

    // Clamp to OBB extents to find closest point
    let closest_x = local_x.clamp(-half.x, half.x);
    let closest_y = local_y.clamp(-half.y, half.y);

    // Distance from circle center to closest point
    let dx = local_x - closest_x;
    let dy = local_y - closest_y;
    (dx * dx + dy * dy) < radius * radius
}
