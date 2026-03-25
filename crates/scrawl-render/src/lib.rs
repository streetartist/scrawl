//! Scrawl Render - 2D rendering plugin
//!
//! Rendering systems run in Update (every frame for smooth visuals).
//! Game logic runs in FixedUpdate (see scrawl-core).

pub mod camera;
pub mod collision_debug;
pub mod fps_overlay;
pub mod mask_gen;
pub mod pen;
pub mod sprite_render;
pub mod svg_loader;

use bevy::prelude::*;

pub struct ScrawlRenderPlugin;

impl Plugin for ScrawlRenderPlugin {
    fn build(&self, app: &mut App) {
        // SVG asset loader
        app.add_plugins(svg_loader::SvgLoaderPlugin);

        app.add_systems(Startup, camera::setup_camera);

        // Runs every render frame
        app.add_systems(
            Update,
            (
                camera::update_camera_viewport,
                sprite_render::update_sprite_visibility,
                sprite_render::update_sprite_costume,
                sprite_render::update_sprite_color,
                pen::update_pen_paths,
                mask_gen::generate_collision_masks,
                collision_debug::draw_collision_debug,
            ),
        );

        app.add_plugins(fps_overlay::FpsOverlayPlugin);
    }
}
