//! Scrawl Particles - GPU-accelerated particle system.
//!
//! Built on bevy_hanabi for efficient GPU particle rendering.

use bevy::prelude::*;
use bevy_hanabi::prelude::*;

/// Particle system plugin.
pub struct ScrawlParticlePlugin;

impl Plugin for ScrawlParticlePlugin {
    fn build(&self, app: &mut App) {
        app.add_plugins(HanabiPlugin);
    }
}

/// High-level particle emitter configuration (maps to bevy_hanabi EffectAsset).
#[derive(Debug, Clone)]
pub struct ParticleConfig {
    /// Max particles alive at once.
    pub capacity: u32,
    /// Particles spawned per second.
    pub spawn_rate: f32,
    /// Particle lifetime in seconds.
    pub lifetime: f32,
    /// Initial speed range.
    pub speed_min: f32,
    pub speed_max: f32,
    /// Particle size.
    pub size: f32,
    /// Start color.
    pub color_start: Color,
    /// End color (fades to this over lifetime).
    pub color_end: Color,
    /// Gravity applied to particles.
    pub gravity: Vec3,
    /// Emission shape radius (circular emission).
    pub emit_radius: f32,
}

impl Default for ParticleConfig {
    fn default() -> Self {
        Self {
            capacity: 1000,
            spawn_rate: 50.0,
            lifetime: 2.0,
            speed_min: 20.0,
            speed_max: 80.0,
            size: 4.0,
            color_start: Color::srgba(1.0, 0.8, 0.2, 1.0),
            color_end: Color::srgba(1.0, 0.2, 0.0, 0.0),
            gravity: Vec3::new(0.0, -50.0, 0.0),
            emit_radius: 5.0,
        }
    }
}

/// Spawn a particle emitter entity from a ParticleConfig.
pub fn spawn_particle_emitter(
    commands: &mut Commands,
    effects: &mut Assets<EffectAsset>,
    config: &ParticleConfig,
    position: Vec3,
) -> Entity {
    let writer = ExprWriter::new();

    let age = writer.lit(0.0).expr();
    let init_age = SetAttributeModifier::new(Attribute::AGE, age);

    let lifetime = writer.lit(config.lifetime).expr();
    let init_lifetime = SetAttributeModifier::new(Attribute::LIFETIME, lifetime);

    let spawner = Spawner::rate(config.spawn_rate.into());

    let effect = EffectAsset::new(config.capacity, spawner, writer.finish())
        .with_name("scrawl_particle")
        .init(init_age)
        .init(init_lifetime);

    let effect_handle = effects.add(effect);

    commands
        .spawn((
            ParticleEffectBundle {
                effect: ParticleEffect::new(effect_handle),
                transform: Transform::from_translation(position),
                ..default()
            },
        ))
        .id()
}
