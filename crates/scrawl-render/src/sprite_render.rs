//! Sprite rendering systems.
//!
//! Syncs CostumeSet, Visible, SpriteColor components to Bevy's Sprite rendering.

use bevy::prelude::*;
use scrawl_core::components::{CostumeSet, SpriteColor, Visible};

/// Updates Bevy Visibility based on the Scrawl Visible component.
pub fn update_sprite_visibility(
    mut query: Query<(&Visible, &mut Visibility), Changed<Visible>>,
) {
    for (visible, mut vis) in query.iter_mut() {
        *vis = if visible.0 {
            Visibility::Inherited
        } else {
            Visibility::Hidden
        };
    }
}

/// Updates the sprite's texture when the costume changes.
pub fn update_sprite_costume(
    mut query: Query<(&CostumeSet, &mut Sprite), Changed<CostumeSet>>,
) {
    for (costume_set, mut sprite) in query.iter_mut() {
        if let Some(costume) = costume_set.current_costume() {
            if let Some(ref handle) = costume.handle {
                sprite.image = handle.clone();
            }
        }
    }
}

/// Updates sprite color tint.
pub fn update_sprite_color(
    mut query: Query<(&SpriteColor, &mut Sprite), Changed<SpriteColor>>,
) {
    for (color, mut sprite) in query.iter_mut() {
        sprite.color = color.0;
    }
}
