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
        (
            Entity,
            &PhysicsProps,
            Option<&PhysicsBodyConfig>,
            Option<&Velocity2D>,
            Option<&Children>,
        ),
        (Added<PhysicsProps>, Without<RapierInitialized>),
    >,
    shapes: Query<(Entity, &PhysicsShape)>,
) {
    for (entity, props, config, initial_velocity, children) in query.iter() {
        let body_type = match props.body_type {
            PhysicsBodyType::Dynamic => RigidBody::Dynamic,
            PhysicsBodyType::Static => RigidBody::Fixed,
            PhysicsBodyType::Kinematic => RigidBody::KinematicPositionBased,
        };

        let velocity = initial_velocity.cloned().unwrap_or_default();
        commands.entity(entity).insert((
            body_type,
            Velocity {
                linvel: velocity.linear,
                angvel: velocity.angular,
            },
            GravityScale(props.gravity_scale),
            Damping {
                linear_damping: config.map(|value| value.linear_damp).unwrap_or(0.0),
                angular_damping: config.map(|value| value.angular_damp).unwrap_or(0.0),
            },
            Restitution::coefficient(props.restitution),
            Friction::coefficient(props.friction),
            RapierInitialized,
        ));

        if let Some(config) = config {
            commands
                .entity(entity)
                .insert(AdditionalMassProperties::Mass(config.mass.max(0.001)));
            if !config.can_sleep {
                commands.entity(entity).insert(Sleeping::disabled());
            } else if config.sleeping {
                commands.entity(entity).insert(Sleeping {
                    sleeping: true,
                    ..default()
                });
            }
            if config.freeze {
                commands.entity(entity).insert(RigidBodyDisabled);
            }
        }

        let mut has_child_shape = false;
        if let Some(children) = children {
            for &child in children.iter() {
                let Ok((shape_entity, shape)) = shapes.get(child) else {
                    continue;
                };
                has_child_shape = true;
                let mut collider_entity = commands.entity(shape_entity);
                collider_entity.insert((
                    collider_from_shape(shape),
                    Friction::coefficient(props.friction),
                    Restitution::coefficient(props.restitution),
                    CollisionGroups::new(
                        Group::from_bits_truncate(
                            config.map(|value| value.collision_layer).unwrap_or(1),
                        ),
                        Group::from_bits_truncate(
                            config.map(|value| value.collision_mask).unwrap_or(1),
                        ),
                    ),
                ));
                if shape.disabled {
                    collider_entity.insert(ColliderDisabled);
                }
            }
        }

        // A body without a CollisionShape2D still gets a small fallback box,
        // matching the Python bounding-rect fallback.
        if !has_child_shape {
            commands.entity(entity).insert((
                Collider::cuboid(16.0, 16.0),
                CollisionGroups::new(
                    Group::from_bits_truncate(
                        config.map(|value| value.collision_layer).unwrap_or(1),
                    ),
                    Group::from_bits_truncate(
                        config.map(|value| value.collision_mask).unwrap_or(1),
                    ),
                ),
            ));
        }
    }
}

fn collider_from_shape(shape: &PhysicsShape) -> Collider {
    match shape.kind {
        CollisionKind::Circle => Collider::ball(
            shape
                .radius
                .or_else(|| shape.size.map(|size| size.x.max(size.y) / 2.0))
                .unwrap_or(16.0)
                .abs(),
        ),
        // Mask and unsupported polygon shapes intentionally use their AABB in
        // this first native-physics mapping. Pixel masks remain available for
        // Sprite collision events.
        CollisionKind::Rect | CollisionKind::Mask => {
            let size = shape.size.unwrap_or(Vec2::new(32.0, 32.0));
            Collider::cuboid(size.x.abs() / 2.0, size.y.abs() / 2.0)
        }
    }
}

/// System: apply changed Python shape definitions to initialized Rapier colliders.
pub fn sync_physics_shapes_to_rapier(
    mut commands: Commands,
    mut query: Query<
        (Entity, &PhysicsShape, &mut Collider),
        (With<RapierColliderHandle>, Changed<PhysicsShape>),
    >,
) {
    for (entity, shape, mut collider) in query.iter_mut() {
        *collider = collider_from_shape(shape);
        if shape.disabled {
            commands.entity(entity).insert(ColliderDisabled);
        } else {
            commands.entity(entity).remove::<ColliderDisabled>();
        }
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
    mut commands: Commands,
    mut query: Query<
        (
            Entity,
            &PhysicsProps,
            Option<&PhysicsBodyConfig>,
            &mut GravityScale,
            &mut Damping,
            &mut Restitution,
            &mut Friction,
            &mut RigidBody,
            Option<&Children>,
            Option<&mut CollisionGroups>,
        ),
        (
            With<RapierInitialized>,
            Or<(Changed<PhysicsProps>, Changed<PhysicsBodyConfig>)>,
        ),
    >,
    shapes: Query<(), With<PhysicsShape>>,
) {
    for (
        entity,
        props,
        config,
        mut gravity,
        mut damping,
        mut restitution,
        mut friction,
        mut rigid_body,
        children,
        mut body_groups,
    ) in query.iter_mut()
    {
        let body_type = match props.body_type {
            PhysicsBodyType::Dynamic => RigidBody::Dynamic,
            PhysicsBodyType::Static => RigidBody::Fixed,
            PhysicsBodyType::Kinematic => RigidBody::KinematicPositionBased,
        };
        *rigid_body = body_type;
        gravity.0 = props.gravity_scale;
        damping.linear_damping = config.map(|value| value.linear_damp).unwrap_or(0.0);
        damping.angular_damping = config.map(|value| value.angular_damp).unwrap_or(0.0);
        restitution.coefficient = props.restitution;
        friction.coefficient = props.friction;

        let groups = collision_groups(config);
        if let Some(body_groups) = body_groups.as_deref_mut() {
            *body_groups = groups;
        }
        if let Some(children) = children {
            for &child in children.iter() {
                if shapes.get(child).is_ok() {
                    commands.entity(child).insert((
                        Friction::coefficient(props.friction),
                        Restitution::coefficient(props.restitution),
                        groups,
                    ));
                }
            }
        }

        if let Some(config) = config {
            commands
                .entity(entity)
                .insert(AdditionalMassProperties::Mass(config.mass.max(0.001)));
            if !config.can_sleep {
                commands.entity(entity).insert(Sleeping::disabled());
            } else {
                commands.entity(entity).insert(Sleeping {
                    sleeping: config.sleeping,
                    ..default()
                });
            }
            if config.freeze {
                commands.entity(entity).insert(RigidBodyDisabled);
            } else {
                commands.entity(entity).remove::<RigidBodyDisabled>();
            }
        }
    }
}

fn collision_groups(config: Option<&PhysicsBodyConfig>) -> CollisionGroups {
    CollisionGroups::new(
        Group::from_bits_truncate(config.map(|value| value.collision_layer).unwrap_or(1)),
        Group::from_bits_truncate(config.map(|value| value.collision_mask).unwrap_or(1)),
    )
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ScrawlPhysicsPlugin;
    use scrawl_core::resources::ScrawlConfig;
    use scrawl_core::ScrawlCorePlugin;

    #[test]
    fn initializes_body_and_child_colliders_in_fixed_schedule() {
        let mut app = App::new();
        app.add_plugins(MinimalPlugins);
        app.insert_resource(ScrawlConfig::default());
        app.init_resource::<ButtonInput<KeyCode>>();
        app.init_resource::<ButtonInput<MouseButton>>();
        app.add_plugins((ScrawlCorePlugin, ScrawlPhysicsPlugin));

        let body = app
            .world_mut()
            .spawn((
                Transform::default(),
                GlobalTransform::default(),
                Transform2D::new(100.0, 40.0),
                PhysicsProps {
                    body_type: PhysicsBodyType::Static,
                    ..default()
                },
                PhysicsBodyConfig::default(),
                Velocity2D::default(),
            ))
            .id();
        let shape = app
            .world_mut()
            .spawn((
                Transform::default(),
                GlobalTransform::default(),
                PhysicsShape {
                    kind: CollisionKind::Circle,
                    size: None,
                    radius: Some(8.0),
                    disabled: false,
                },
            ))
            .id();
        let visual = app
            .world_mut()
            .spawn((Sprite::default(), Transform::from_xyz(0.0, 0.0, 0.0)))
            .id();
        app.world_mut().entity_mut(body).add_child(shape);
        app.world_mut().entity_mut(body).add_child(visual);

        app.update();
        app.world_mut().run_schedule(FixedUpdate);
        app.world_mut().run_schedule(FixedUpdate);

        assert!(app.world().get::<RapierInitialized>(body).is_some());
        assert!(app.world().get::<RigidBody>(body).is_some());
        assert!(app.world().get::<Collider>(shape).is_some());
        let body_transform = app.world().get::<Transform>(body).unwrap();
        assert_eq!(
            Vec2::new(body_transform.translation.x, body_transform.translation.y),
            Vec2::new(100.0, 40.0)
        );
        let visual_transform = app.world().get::<Transform>(visual).unwrap();
        assert_eq!(
            Vec2::new(
                visual_transform.translation.x,
                visual_transform.translation.y
            ),
            Vec2::ZERO
        );

        *app.world_mut()
            .entity_mut(shape)
            .get_mut::<PhysicsShape>()
            .unwrap() = PhysicsShape {
            kind: CollisionKind::Rect,
            size: Some(Vec2::new(20.0, 12.0)),
            radius: None,
            disabled: false,
        };
        app.world_mut().run_schedule(FixedUpdate);
        let collider = app.world().get::<Collider>(shape).unwrap();
        assert_eq!(
            collider.as_cuboid().unwrap().half_extents(),
            Vec2::new(10.0, 6.0)
        );
    }

    #[test]
    fn dynamic_body_falls_onto_static_floor() {
        let mut app = App::new();
        app.add_plugins(MinimalPlugins);
        app.insert_resource(ScrawlConfig::default());
        app.init_resource::<ButtonInput<KeyCode>>();
        app.init_resource::<ButtonInput<MouseButton>>();
        app.add_plugins((ScrawlCorePlugin, ScrawlPhysicsPlugin));
        app.insert_resource(TimestepMode::Fixed {
            dt: 1.0 / 60.0,
            substeps: 1,
        });

        let floor = app
            .world_mut()
            .spawn((
                Transform::from_xyz(400.0, 40.0, 0.0),
                GlobalTransform::default(),
                Transform2D::new(400.0, 40.0),
                PhysicsProps {
                    body_type: PhysicsBodyType::Static,
                    restitution: 0.0,
                    friction: 0.8,
                    ..default()
                },
                PhysicsBodyConfig::default(),
                Velocity2D::default(),
            ))
            .id();
        let floor_shape = app
            .world_mut()
            .spawn((
                Transform::default(),
                GlobalTransform::default(),
                PhysicsShape {
                    kind: CollisionKind::Rect,
                    size: Some(Vec2::new(720.0, 24.0)),
                    radius: None,
                    disabled: false,
                },
            ))
            .id();
        app.world_mut().entity_mut(floor).add_child(floor_shape);

        let ball = app
            .world_mut()
            .spawn((
                Transform::from_xyz(400.0, 500.0, 0.0),
                GlobalTransform::default(),
                Transform2D::new(400.0, 500.0),
                PhysicsProps {
                    restitution: 0.0,
                    friction: 0.8,
                    ..default()
                },
                PhysicsBodyConfig {
                    can_sleep: false,
                    ..default()
                },
                Velocity2D::default(),
            ))
            .id();
        let ball_shape = app
            .world_mut()
            .spawn((
                Transform::default(),
                GlobalTransform::default(),
                PhysicsShape {
                    kind: CollisionKind::Circle,
                    size: None,
                    radius: Some(18.0),
                    disabled: false,
                },
            ))
            .id();
        app.world_mut().entity_mut(ball).add_child(ball_shape);

        app.update();
        for _ in 0..180 {
            app.world_mut().run_schedule(FixedUpdate);
        }

        let transform = app.world().get::<Transform>(ball).unwrap();
        assert!(
            (55.0..90.0).contains(&transform.translation.y),
            "ball should rest near the floor, got y={}",
            transform.translation.y
        );
    }
}
