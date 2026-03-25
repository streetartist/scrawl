//! Camera setup for the Scrawl engine.
//!
//! Letterbox scaling: game logic runs at design resolution,
//! fullscreen adds black bars to maintain aspect ratio.

use bevy::prelude::*;
use bevy::render::camera::{ClearColorConfig, Viewport};
use scrawl_core::resources::ScrawlConfig;

/// Marker component for the main Scrawl camera.
#[derive(Component)]
pub struct ScrawlCamera;

/// Resource: the scene background color for the camera to clear to.
#[derive(Resource)]
pub struct SceneBackgroundColor(pub Color);

impl Default for SceneBackgroundColor {
    fn default() -> Self {
        Self(Color::WHITE)
    }
}

/// Sets up the 2D camera on startup.
pub fn setup_camera(
    mut commands: Commands,
    config: Res<ScrawlConfig>,
    bg: Option<Res<SceneBackgroundColor>>,
) {
    let bg_color = bg.map(|b| b.0).unwrap_or(Color::WHITE);

    commands.spawn((
        Camera2d,
        ScrawlCamera,
        Camera {
            // Camera clears its viewport to the scene background color.
            // ClearColor (BLACK) handles the area outside the viewport (letterbox bars).
            clear_color: ClearColorConfig::Custom(bg_color),
            ..default()
        },
        OrthographicProjection {
            scaling_mode: bevy::render::camera::ScalingMode::Fixed {
                width: config.width as f32,
                height: config.height as f32,
            },
            ..OrthographicProjection::default_2d()
        },
        Transform::from_xyz(
            config.width as f32 / 2.0,
            config.height as f32 / 2.0,
            1000.0,
        ),
    ));

    log::info!(
        "Scrawl camera initialized: {}x{} (letterbox)",
        config.width,
        config.height
    );
}

/// System: update camera viewport for letterbox on resize/fullscreen.
pub fn update_camera_viewport(
    config: Res<ScrawlConfig>,
    windows: Query<&Window>,
    mut cameras: Query<&mut Camera, With<ScrawlCamera>>,
) {
    let Ok(window) = windows.get_single() else { return };
    let Ok(mut camera) = cameras.get_single_mut() else { return };

    let window_w = window.physical_width();
    let window_h = window.physical_height();
    if window_w == 0 || window_h == 0 {
        return;
    }

    let design_aspect = config.width as f32 / config.height as f32;
    let window_aspect = window_w as f32 / window_h as f32;

    // If aspect ratios match, no viewport needed (fill entire window)
    if (window_aspect - design_aspect).abs() < 0.02 {
        camera.viewport = None;
        return;
    }

    let (viewport_w, viewport_h, offset_x, offset_y) = if window_aspect > design_aspect {
        // Wider → black bars left/right
        let h = window_h;
        let w = (h as f32 * design_aspect) as u32;
        let x = (window_w - w) / 2;
        (w, h, x, 0)
    } else {
        // Taller → black bars top/bottom
        let w = window_w;
        let h = (w as f32 / design_aspect) as u32;
        let y = (window_h - h) / 2;
        (w, h, 0, y)
    };

    camera.viewport = Some(Viewport {
        physical_position: UVec2::new(offset_x, offset_y),
        physical_size: UVec2::new(viewport_w, viewport_h),
        ..default()
    });
}
