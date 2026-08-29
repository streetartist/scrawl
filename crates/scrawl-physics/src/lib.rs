//! Scrawl Physics - Rapier2D integration for the Scrawl engine.
//!
//! This crate bridges scrawl-core's physics components (`PhysicsProps`,
//! `CollisionShape`, `Velocity2D`, `Transform2D`) with the bevy_rapier2d
//! physics simulation.

pub mod sync;

use bevy::prelude::*;
use bevy_rapier2d::prelude::*;
use scrawl_core::schedule::ScrawlSet;

/// Plugin that sets up Rapier2D physics and the sync systems between
/// Scrawl components and Rapier components.
pub struct ScrawlPhysicsPlugin;

impl Plugin for ScrawlPhysicsPlugin {
    fn build(&self, app: &mut App) {
        // Add Rapier plugin with 100 pixels per meter, debug render disabled.
        app.add_plugins(
            RapierPhysicsPlugin::<NoUserData>::pixels_per_meter(100.0).in_fixed_schedule(),
        );

        // Python and core scripts run before this set. Rapier's own systems run
        // in the same FixedUpdate schedule, so initialization/configuration must
        // happen before its SyncBackend phase and writeback must happen after it.
        app.add_systems(
            FixedUpdate,
            (
                sync::init_rapier_bodies,
                sync::sync_physics_shapes_to_rapier,
                sync::sync_velocity_to_rapier,
                sync::sync_physics_props_to_rapier,
            )
                .chain()
                .in_set(ScrawlSet::Physics)
                .before(PhysicsSet::SyncBackend),
        );
        app.add_systems(
            FixedUpdate,
            sync::sync_rapier_transform_back
                .in_set(ScrawlSet::Physics)
                .after(PhysicsSet::Writeback),
        );

        log::info!("ScrawlPhysicsPlugin initialized (100 px/m, debug render off)");
    }
}
