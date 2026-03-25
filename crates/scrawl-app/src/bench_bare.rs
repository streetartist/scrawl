//! Bare Bevy benchmark — no Python, no scrawl plugins, just 2 sprites.
//! Run: cargo run --release --bin bench-bare

use bevy::prelude::*;
use bevy::diagnostic::{DiagnosticsStore, FrameTimeDiagnosticsPlugin};

fn main() {
    App::new()
        .add_plugins(DefaultPlugins.set(WindowPlugin {
            primary_window: Some(Window {
                title: "Bare Bevy Bench".into(),
                resolution: (800.0, 600.0).into(),
                present_mode: bevy::window::PresentMode::AutoNoVsync,
                ..default()
            }),
            ..default()
        }))
        .add_plugins(FrameTimeDiagnosticsPlugin::default())
        .add_systems(Startup, setup)
        .add_systems(Update, (move_sprites, show_fps))
        .run();
}

fn setup(mut commands: Commands) {
    commands.spawn(Camera2d);

    // Sprite 1
    commands.spawn((
        Sprite {
            color: Color::srgb(1.0, 0.4, 0.4),
            custom_size: Some(Vec2::new(50.0, 50.0)),
            ..default()
        },
        Transform::from_xyz(400.0, 300.0, 0.0),
    ));

    // Sprite 2
    commands.spawn((
        Sprite {
            color: Color::srgb(0.4, 0.4, 1.0),
            custom_size: Some(Vec2::new(75.0, 75.0)),
            ..default()
        },
        Transform::from_xyz(200.0, 200.0, 0.0),
    ));
}

fn move_sprites(mut query: Query<&mut Transform, With<Sprite>>, time: Res<Time>) {
    for mut t in query.iter_mut() {
        t.translation.x += 60.0 * time.delta_secs();
        if t.translation.x > 850.0 {
            t.translation.x = -50.0;
        }
    }
}

fn show_fps(diagnostics: Res<DiagnosticsStore>, mut windows: Query<&mut Window>) {
    if let Ok(mut window) = windows.get_single_mut() {
        if let Some(fps) = diagnostics
            .get(&FrameTimeDiagnosticsPlugin::FPS)
            .and_then(|d| d.smoothed())
        {
            window.title = format!("Bare Bevy Bench | FPS: {:.0}", fps);
        }
    }
}
