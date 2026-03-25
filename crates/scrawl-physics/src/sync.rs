//! Sync systems between scrawl-core components and Rapier2D.

use bevy::prelude::*;
use bevy_rapier2d::prelude::*;
use scrawl_core::components::*;

/// Marker: entity already has Rapier components initialized.
#[derive(Component)]
pub struct RapierInitialized;

/// System: when PhysicsProps is added, insert Rapier RigidBody + Collider.
pub fn init_rapier_bodies(
    mut commands: Commands,
    query: Query<
        (Entity, &PhysicsProps, &CollisionShape, &Transform2D),
        (Added<PhysicsProps>, Without<RapierInitialized>),
    >,
    sprites: Query<&Sprite>,
) {
    for (entity, props, shape, t2d) in query.iter() {
        let body_type = match props.body_type {
            PhysicsBodyType::Dynamic => RigidBody::Dynamic,
            PhysicsBodyType::Static => RigidBody::Fixed,
            PhysicsBodyType::Kinematic => RigidBody::KinematicPositionBased,
        };

        // Determine collider from CollisionShape
        let half_size = sprites
            .get(entity)
            .ok()
            .and_then(|s| s.custom_size)
            .unwrap_or(Vec2::new(50.0, 50.0))
            * t2d.scale
            / 2.0;

        let collider = match shape.kind {
            CollisionKind::Circle => {
                let radius = shape.radius.unwrap_or(half_size.x.max(half_size.y));
                Collider::ball(radius)
            }
            _ => Collider::cuboid(half_size.x, half_size.y),
        };

        commands.entity(entity).insert((
            body_type,
            collider,
            Velocity::default(),
            GravityScale(props.gravity_scale),
            Damping {
                linear_damping: props.friction * 50.0,
                angular_damping: props.friction * 50.0,
            },
            Restitution::coefficient(props.restitution),
            Friction::coefficient(props.friction),
            RapierInitialized,
        ));
    }
}

/// System: sync scrawl Velocity2D → Rapier Velocity each frame.
pub fn sync_velocity_to_rapier(
    mut query: Query<(&Velocity2D, &mut Velocity), (With<RapierInitialized>, Changed<Velocity2D>)>,
) {
    for (v2d, mut rapier_vel) in query.iter_mut() {
        rapier_vel.linvel = v2d.linear;
        rapier_vel.angvel = v2d.angular;
    }
}

/// System: sync changed PhysicsProps → Rapier components.
pub fn sync_physics_props_to_rapier(
    mut query: Query<
        (&PhysicsProps, &mut GravityScale, &mut Damping, &mut Restitution, &mut Friction),
        (With<RapierInitialized>, Changed<PhysicsProps>),
    >,
) {
    for (props, mut gravity, mut damping, mut restitution, mut friction) in query.iter_mut() {
        gravity.0 = props.gravity_scale;
        damping.linear_damping = props.friction * 50.0;
        damping.angular_damping = props.friction * 50.0;
        restitution.coefficient = props.restitution;
        friction.coefficient = props.friction;
    }
}

/// System: sync Rapier transform back → scrawl Transform2D + Velocity2D.
pub fn sync_rapier_transform_back(
    mut query: Query<
        (&Transform, &Velocity, &mut Transform2D, &mut Velocity2D),
        (With<RapierInitialized>, Changed<Transform>),
    >,
) {
    for (transform, rapier_vel, mut t2d, mut v2d) in query.iter_mut() {
        t2d.position.x = transform.translation.x;
        t2d.position.y = transform.translation.y;
        let (_, _, z) = transform.rotation.to_euler(EulerRot::XYZ);
        t2d.rotation_degrees = 90.0 - z.to_degrees();

        v2d.linear = rapier_vel.linvel;
        v2d.angular = rapier_vel.angvel;
    }
}
