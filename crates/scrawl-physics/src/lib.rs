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
            RapierPhysicsPlugin::<NoUserData>::pixels_per_meter(100.0),
        );

        // Register sync systems in the Physics set.
        app.add_systems(
            Update,
            (
                sync::init_rapier_bodies,
                sync::sync_velocity_to_rapier,
                sync::sync_physics_props_to_rapier,
                sync::sync_rapier_transform_back,
            )
                .chain()
                .in_set(ScrawlSet::Physics),
        );

        log::info!("ScrawlPhysicsPlugin initialized (100 px/m, debug render off)");
    }
}
