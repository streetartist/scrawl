//! Scrawl Core - Core ECS components, resources, events, and scheduling
//!
//! All game logic (input, scripts, physics, collision) runs in FixedUpdate
//! at the target FPS rate. Rendering runs in Update at GPU speed.

pub mod collision;
pub mod components;
pub mod events;
pub mod input;
pub mod resources;
pub mod schedule;
pub mod scene;

use bevy::prelude::*;

/// The core plugin that registers all components, resources, events, and schedules.
pub struct ScrawlCorePlugin;

impl Plugin for ScrawlCorePlugin {
    fn build(&self, app: &mut App) {
        // Register events
        app.add_event::<events::BroadcastEvent>()
            .add_event::<events::EdgeCollisionEvent>()
            .add_event::<events::SpriteCollisionEvent>()
            .add_event::<events::KeyInputEvent>()
            .add_event::<events::MouseInputEvent>()
            .add_event::<events::SpriteClickedEvent>()
            .add_event::<events::SceneChangeEvent>();

        // Initialize resources
        app.init_resource::<resources::ScrawlConfig>()
            .init_resource::<resources::BroadcastQueue>()
            .init_resource::<resources::MouseState>()
            .init_resource::<resources::SceneManager>()
            .init_resource::<resources::KeyState>()
            .init_resource::<resources::InputBuffer>();

        // Set fixed timestep from config at startup
        app.add_systems(Startup, init_fixed_timestep);

        // Configure system sets in FixedUpdate (game logic at fixed rate)
        app.configure_sets(
            FixedUpdate,
            (
                schedule::ScrawlSet::Input,
                schedule::ScrawlSet::ScriptExec,
                schedule::ScrawlSet::Physics,
                schedule::ScrawlSet::CollisionDetect,
                schedule::ScrawlSet::Animation,
                schedule::ScrawlSet::Particles,
                schedule::ScrawlSet::Navigation,
                schedule::ScrawlSet::PostUpdate,
            )
                .chain(),
        );

        // Input gathering in Update (reads Bevy ButtonInput correctly)
        app.add_systems(Update, input::gather_input);

        // Game logic in FixedUpdate
        app.add_systems(
            FixedUpdate,
            (
                // Dispatch buffered input → events
                input::dispatch_input_events.in_set(schedule::ScrawlSet::Input),
                // Collision detection
                (
                    collision::detect_edge_collisions,
                    collision::detect_sprite_collisions,
                )
                    .in_set(schedule::ScrawlSet::CollisionDetect),
                // Cleanup
                (
                    scene::process_broadcast_queue,
                    scene::cleanup_speech_bubbles,
                )
                    .in_set(schedule::ScrawlSet::PostUpdate),
            ),
        );

        // Transform sync in Update (smooth rendering)
        app.add_systems(Update, scene::sync_transform2d_to_bevy);
    }
}

/// Set Bevy's fixed timestep to match the target FPS from ScrawlConfig.
fn init_fixed_timestep(config: Res<resources::ScrawlConfig>, mut time: ResMut<Time<Fixed>>) {
    let hz = if config.fps > 0 { config.fps } else { 60 };
    time.set_timestep_hz(hz as f64);
    log::info!("Fixed timestep set to {}hz ({}fps)", hz, hz);
}

/// Prelude for convenient imports
pub mod prelude {
    pub use crate::components::*;
    pub use crate::events::*;
    pub use crate::resources::*;
    pub use crate::schedule::*;
    pub use crate::ScrawlCorePlugin;
}
