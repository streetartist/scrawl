//! Debug FPS overlay using Bevy's built-in FpsOverlayPlugin.

use bevy::prelude::*;
use bevy::dev_tools::fps_overlay::{FpsOverlayConfig, FpsOverlayPlugin as BevyFpsOverlay};

pub struct FpsOverlayPlugin;

impl Plugin for FpsOverlayPlugin {
    fn build(&self, app: &mut App) {
        app.add_plugins(BevyFpsOverlay {
            config: FpsOverlayConfig {
                text_config: TextFont {
                    font_size: 20.0,
                    ..default()
                },
                text_color: Color::srgb(0.0, 1.0, 0.0),
                enabled: false, // Start disabled, enable in Startup if debug
            },
        });
        app.add_systems(Startup, enable_if_debug);
    }
}

fn enable_if_debug(
    config: Res<scrawl_core::resources::ScrawlConfig>,
    mut fps_config: ResMut<FpsOverlayConfig>,
) {
    if config.debug {
        fps_config.enabled = true;
    }
}
