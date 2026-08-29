//! Runtime integration - connects Python scripts to the Bevy ECS.
//!
//! All Python interaction happens in a single exclusive system per frame,
//! acquiring the GIL only once to minimize overhead.

use bevy::hierarchy::DespawnRecursiveExt;
use bevy::prelude::*;
use bevy_kira_audio::Audio;
use pyo3::prelude::*;
use scrawl_audio::AudioManager;
use std::collections::{HashMap, HashSet};
use std::time::{Duration, Instant};

use scrawl_core::components::*;
use scrawl_core::events::*;
use scrawl_core::schedule::ScrawlSet;

const DIRTY_TRANSFORM: u8 = 1 << 0;
const DIRTY_VISIBLE: u8 = 1 << 1;
const DIRTY_COLOR: u8 = 1 << 2;
const DIRTY_COSTUME: u8 = 1 << 3;
const DIRTY_PEN: u8 = 1 << 4;
const DIRTY_DIMENSIONS: u8 = 1 << 5;
const DIRTY_DRAW_ORDER: u8 = 1 << 6;
const DIRTY_ALL: u8 = (1 << 7) - 1;

/// Stable link from a Python Node to its Bevy entity.
#[derive(Component, Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct PythonNodeId(pub u64);

/// A registered Python sprite instance with its handlers.
#[derive(Debug)]
pub struct PythonSpriteInstance {
    pub node_id: u64,
    pub py_object: Py<PyAny>,
    pub entity: Entity,
    pub coroutines: HashMap<String, Py<PyAny>>,
    pub wake_times: HashMap<String, Instant>,
    pub handlers: Vec<(String, HandlerKind)>,
}

#[derive(Debug, Clone)]
pub enum HandlerKind {
    Main,
    Clone,
    Key { key: String, mode: String },
    Broadcast { event: String },
    SpriteClicked,
    EdgeCollision { edge: String },
    SpriteCollision { target: String },
    Mouse { button: u32, mode: String },
}

/// Resource holding all Python runtime state.
#[derive(Resource)]
pub struct PythonRuntime {
    pub sprites: Vec<PythonSpriteInstance>,
    pub nodes: HashMap<u64, Entity>,
    pub node_objects: HashMap<u64, Py<PyAny>>,
    pub budget_ms: u64,
}

impl Default for PythonRuntime {
    fn default() -> Self {
        Self {
            sprites: Vec::new(),
            nodes: HashMap::new(),
            node_objects: HashMap::new(),
            budget_ms: 8,
        }
    }
}

/// Bevy plugin that adds the Python runtime systems.
pub struct PythonRuntimePlugin;

impl Plugin for PythonRuntimePlugin {
    fn build(&self, app: &mut App) {
        app.init_resource::<PythonRuntime>();
        // Single exclusive system — one GIL acquisition per frame
        app.add_systems(
            FixedUpdate,
            python_frame_system.in_set(ScrawlSet::ScriptExec),
        );
        app.add_systems(
            FixedUpdate,
            sync_physics_nodes_to_python.after(ScrawlSet::Physics),
        );
    }
}

/// Single exclusive system that does ALL Python work in one GIL acquisition.
fn python_frame_system(world: &mut World) {
    let fixed_delta = world
        .get_resource::<Time<Fixed>>()
        .map(|time| time.delta_secs())
        .unwrap_or(1.0 / 60.0);

    // Generic Node2D descendants (including physics bodies) do not live in the
    // sprite handler list. Run the scene tree callback once so kinematic bodies
    // and user-defined node logic participate in the same fixed tick.
    let scene_roots: Vec<Py<PyAny>> = {
        let runtime = world.resource::<PythonRuntime>();
        Python::with_gil(|py| {
            runtime
                .node_objects
                .values()
                .filter_map(|object| {
                    let bound = object.bind(py);
                    let kind = bound
                        .getattr("_scrawl_node_kind")
                        .and_then(|value| value.extract::<String>())
                        .ok()?;
                    (kind == "scene").then(|| object.clone_ref(py))
                })
                .collect()
        })
    };

    // Collect events from the world before acquiring GIL
    let key_events: Vec<KeyInputEvent> = world
        .resource_mut::<Events<KeyInputEvent>>()
        .drain()
        .collect();
    let mouse_events: Vec<MouseInputEvent> = world
        .resource_mut::<Events<MouseInputEvent>>()
        .drain()
        .collect();
    let broadcast_events: Vec<BroadcastEvent> = world
        .resource_mut::<Events<BroadcastEvent>>()
        .drain()
        .collect();
    let edge_events: Vec<EdgeCollisionEvent> = world
        .resource_mut::<Events<EdgeCollisionEvent>>()
        .drain()
        .collect();
    let collision_events: Vec<SpriteCollisionEvent> = world
        .resource_mut::<Events<SpriteCollisionEvent>>()
        .drain()
        .collect();
    let mut clicked_entities: HashSet<Entity> = world
        .resource_mut::<Events<SpriteClickedEvent>>()
        .drain()
        .map(|event| event.0)
        .collect();

    clicked_entities.extend(synthesize_sprite_clicked_entities(world, &mouse_events));

    // Collect entity names for collision lookup
    let mut entity_names: HashMap<Entity, String> = HashMap::new();
    if !collision_events.is_empty() {
        let mut query = world.query::<(Entity, &ScrawlName)>();
        for (e, name) in query.iter(world) {
            entity_names.insert(e, name.0.clone());
        }
    }

    let budget_ms = world.resource::<PythonRuntime>().budget_ms;

    // Temporarily take sprites out of the resource to avoid borrow conflicts
    let mut sprites = std::mem::take(&mut world.resource_mut::<PythonRuntime>().sprites);

    // === Single GIL acquisition for the entire frame ===
    let commands = Python::with_gil(|py| {
        let deadline = Instant::now() + Duration::from_millis(budget_ms);

        for scene in &scene_roots {
            if let Err(error) = scene
                .bind(py)
                .call_method1("_physics_process_tree", (fixed_delta,))
            {
                eprintln!("[Scrawl] Error in scene physics processing: {error}");
            }
        }

        for sprite in sprites.iter_mut() {
            // Clone handlers to avoid borrow conflict with start_handler
            let handlers = sprite.handlers.clone();

            // --- 1. Dispatch key events → start new handler coroutines ---
            for event in &key_events {
                let event_key = format_key_code(event.key);
                let event_mode = match event.mode {
                    InputMode::Pressed => "pressed",
                    InputMode::Released => "released",
                    InputMode::Held => "held",
                };
                for (method_name, kind) in &handlers {
                    if let HandlerKind::Key { key, mode } = kind {
                        if *key == event_key && *mode == event_mode {
                            let coro_key = format!("key_{}_{}", method_name, event_key);
                            if !sprite.coroutines.contains_key(&coro_key) {
                                start_handler(py, sprite, method_name, coro_key);
                            }
                        }
                    }
                }
            }

            // --- 2. Dispatch broadcast events ---
            for ev in &broadcast_events {
                for (method_name, kind) in &handlers {
                    if let HandlerKind::Broadcast { event } = kind {
                        if *event == ev.0 {
                            let coro_key = format!("broadcast_{}_{}", method_name, event);
                            if !sprite.coroutines.contains_key(&coro_key) {
                                start_handler(py, sprite, method_name, coro_key);
                            }
                        }
                    }
                }
            }

            // --- 3. Dispatch edge collision events ---
            for ev in &edge_events {
                if ev.entity != sprite.entity {
                    continue;
                }
                let edge_str = match ev.edge {
                    Edge::Left => "left",
                    Edge::Right => "right",
                    Edge::Top => "top",
                    Edge::Bottom => "bottom",
                };
                for (method_name, kind) in &handlers {
                    if let HandlerKind::EdgeCollision { edge } = kind {
                        if *edge == edge_str || *edge == "any" {
                            let coro_key = format!("edge_{}_{}", method_name, edge_str);
                            if !sprite.coroutines.contains_key(&coro_key) {
                                start_handler(py, sprite, method_name, coro_key);
                            }
                        }
                    }
                }
            }

            // --- 4. Dispatch sprite collision events ---
            for ev in &collision_events {
                let other_entity = if ev.entity_a == sprite.entity {
                    ev.entity_b
                } else if ev.entity_b == sprite.entity {
                    ev.entity_a
                } else {
                    continue;
                };
                let other_name = entity_names
                    .get(&other_entity)
                    .map(|s| s.as_str())
                    .unwrap_or("");
                for (method_name, kind) in &handlers {
                    if let HandlerKind::SpriteCollision { target } = kind {
                        if *target == other_name || *target == "*" {
                            let coro_key = format!("collision_{}_{}", method_name, other_name);
                            if !sprite.coroutines.contains_key(&coro_key) {
                                start_handler(py, sprite, method_name, coro_key);
                            }
                        }
                    }
                }
            }

            // --- 5. Dispatch mouse input events ---
            for event in &mouse_events {
                let Some(event_button) = mouse_button_number(event.button) else {
                    continue;
                };
                let event_mode = match event.mode {
                    InputMode::Pressed => "pressed",
                    InputMode::Released => "released",
                    InputMode::Held => "held",
                };

                for (method_name, kind) in &handlers {
                    if let HandlerKind::Mouse { button, mode } = kind {
                        if *button == event_button && *mode == event_mode {
                            let coro_key =
                                format!("mouse_{}_{}_{}", method_name, event_button, event_mode);
                            if !sprite.coroutines.contains_key(&coro_key) {
                                start_handler(py, sprite, method_name, coro_key);
                            }
                        }
                    }
                }
            }

            // --- 6. Dispatch sprite clicked events ---
            if clicked_entities.contains(&sprite.entity) {
                for (method_name, kind) in &handlers {
                    if matches!(kind, HandlerKind::SpriteClicked) {
                        let coro_key = format!("clicked_{}", method_name);
                        if !sprite.coroutines.contains_key(&coro_key) {
                            start_handler(py, sprite, method_name, coro_key);
                        }
                    }
                }
            }

            // --- 7. Advance all active coroutines ---
            let names: Vec<String> = sprite.coroutines.keys().cloned().collect();
            let mut to_remove = Vec::new();

            for name in &names {
                if Instant::now() > deadline {
                    break;
                }
                // Check wake time
                if let Some(wake) = sprite.wake_times.get(name) {
                    if Instant::now() < *wake {
                        continue;
                    }
                }

                if let Some(gen) = sprite.coroutines.get(name) {
                    match gen.bind(py).call_method0("__next__") {
                        Ok(result) => {
                            let delay_ms: u64 = if result.is_none() {
                                0
                            } else {
                                result.extract().unwrap_or(0)
                            };
                            sprite.wake_times.insert(
                                name.clone(),
                                Instant::now() + Duration::from_millis(delay_ms),
                            );
                        }
                        Err(e) => {
                            if e.is_instance_of::<pyo3::exceptions::PyStopIteration>(py) {
                                to_remove.push(name.clone());
                            } else {
                                eprintln!(
                                    "[Scrawl] Script error in {}.{}: {}",
                                    sprite
                                        .py_object
                                        .bind(py)
                                        .getattr("name")
                                        .map(|n| n.to_string())
                                        .unwrap_or_else(|_| "?".into()),
                                    name,
                                    e
                                );
                                to_remove.push(name.clone());
                            }
                        }
                    }
                }
            }

            for name in to_remove {
                sprite.coroutines.remove(&name);
                sprite.wake_times.remove(&name);
            }

            // --- 8. Sync Python state → ECS (Y-up: Python matches Bevy, no flip) ---
            let obj = sprite.py_object.bind(py);
            let entity = sprite.entity;
            let mut previous_position = None;
            let dirty = obj
                .call_method0("_take_dirty")
                .and_then(|value| value.extract::<u8>())
                .unwrap_or(DIRTY_ALL);

            if dirty & DIRTY_TRANSFORM != 0 {
                if let Some(mut t2d) = world.get_mut::<Transform2D>(entity) {
                    previous_position = Some(t2d.position);
                    if let Ok(x) = obj.getattr("x").and_then(|v| v.extract::<f32>()) {
                        t2d.position.x = x;
                    }
                    if let Ok(y) = obj.getattr("y").and_then(|v| v.extract::<f32>()) {
                        t2d.position.y = y;
                    }
                    if let Ok(dir) = obj.getattr("direction").and_then(|v| v.extract::<f32>()) {
                        t2d.rotation_degrees = dir; // rotation handled in sync_transform2d_to_bevy
                    }
                    if let Ok(size) = obj.getattr("size").and_then(|v| v.extract::<f32>()) {
                        t2d.scale = Vec2::splat(size);
                    }
                }
            }
            if dirty & DIRTY_VISIBLE != 0 {
                if let Some(mut vis) = world.get_mut::<Visible>(entity) {
                    if let Ok(visible) = obj.getattr("visible").and_then(|v| v.extract::<bool>()) {
                        vis.0 = visible;
                    }
                }
            }

            if dirty & DIRTY_COLOR != 0 {
                let has_image_costume = world
                    .get::<CostumeSet>(entity)
                    .and_then(|costumes| costumes.current_costume())
                    .and_then(|costume| costume.handle.as_ref())
                    .is_some();
                if let Some(mut sprite_color) = world.get_mut::<SpriteColor>(entity) {
                    if has_image_costume {
                        sprite_color.0 = Color::WHITE;
                    } else if let Ok((r, g, b)) = obj
                        .getattr("color")
                        .and_then(|v| v.extract::<(u8, u8, u8)>())
                    {
                        sprite_color.0 =
                            Color::srgb(r as f32 / 255.0, g as f32 / 255.0, b as f32 / 255.0);
                    }
                }
            }

            if dirty & (DIRTY_TRANSFORM | DIRTY_PEN) != 0 {
                sync_pen_state_from_python(world, entity, &obj, previous_position);
            }

            // Sync current costume
            if dirty & DIRTY_COSTUME != 0 {
                if let Ok(costume_name) = obj
                    .getattr("_current_costume")
                    .and_then(|v| v.extract::<String>())
                {
                    if let Some(mut costumes) = world.get_mut::<CostumeSet>(entity) {
                        costumes.switch_to(&costume_name);
                    }
                }
            }

            if dirty & DIRTY_DIMENSIONS != 0 {
                let width = obj
                    .getattr("width")
                    .ok()
                    .and_then(|v| v.extract::<Option<f32>>().ok())
                    .flatten();
                let height = obj
                    .getattr("height")
                    .ok()
                    .and_then(|v| v.extract::<Option<f32>>().ok())
                    .flatten();
                let has_image = world
                    .get::<CostumeSet>(entity)
                    .and_then(|costumes| costumes.current_costume())
                    .and_then(|costume| costume.handle.as_ref())
                    .is_some();
                if let Some(mut bevy_sprite) = world.get_mut::<Sprite>(entity) {
                    bevy_sprite.custom_size = custom_sprite_size(width, height, has_image);
                }
            }

            if dirty & DIRTY_DRAW_ORDER != 0 {
                if let Ok(z_index) = obj.getattr("z_index").and_then(|v| v.extract::<i32>()) {
                    if let Some(mut transform) = world.get_mut::<Transform>(entity) {
                        transform.translation.z = z_index as f32;
                    }
                }
            }
        }
        sync_python_nodes(world, py);
        process_python_commands(py)
    });

    // Execute commands on the ECS world
    for cmd in commands {
        match cmd {
            PythonCommand::NodeAdd { node, parent_id } => {
                spawn_dynamic_subtree(world, &node, &mut sprites, parent_id);
            }
            PythonCommand::NodeRemove { node_id, node } => {
                despawn_python_subtree(world, node_id, &node, &mut sprites);
            }
            PythonCommand::NodeReparent { node_id, parent_id } => {
                reparent_python_node(world, node_id, parent_id);
            }
            PythonCommand::Broadcast(event) => {
                world.send_event(BroadcastEvent(event));
            }
            PythonCommand::SetText {
                ptr_id,
                text,
                font_size,
                color,
            } => {
                upsert_text_display(
                    world,
                    &sprites,
                    ptr_id,
                    TextDisplayKind::Persistent,
                    text,
                    font_size,
                    color,
                    0.0,
                    None,
                );
            }
            PythonCommand::Say {
                ptr_id,
                text,
                duration_ms,
            } => {
                upsert_text_display(
                    world,
                    &sprites,
                    ptr_id,
                    TextDisplayKind::Speech,
                    text,
                    18.0,
                    [1.0, 1.0, 1.0],
                    48.0,
                    Some(Instant::now() + Duration::from_millis(duration_ms)),
                );
            }
            PythonCommand::PlaySound { path, volume } => {
                play_sound_command(world, &path, volume);
            }
            PythonCommand::PlayMusic {
                path,
                loops,
                volume,
            } => {
                play_music_command(world, &path, loops, volume);
            }
            PythonCommand::StopMusic => stop_music_command(world),
            PythonCommand::PauseMusic => pause_music_command(world),
            PythonCommand::ResumeMusic => resume_music_command(world),
        }
    }

    sync_text_displays(world, &sprites);

    // Put sprites back
    world.resource_mut::<PythonRuntime>().sprites = sprites;
}

enum PythonCommand {
    NodeAdd {
        node: Py<PyAny>,
        parent_id: Option<u64>,
    },
    NodeRemove {
        node_id: u64,
        node: Py<PyAny>,
    },
    NodeReparent {
        node_id: u64,
        parent_id: u64,
    },
    Broadcast(String),
    SetText {
        ptr_id: usize,
        text: String,
        font_size: f32,
        color: [f32; 3],
    },
    Say {
        ptr_id: usize,
        text: String,
        duration_ms: u64,
    },
    PlaySound {
        path: String,
        volume: Option<f64>,
    },
    PlayMusic {
        path: String,
        loops: i32,
        volume: Option<f64>,
    },
    StopMusic,
    PauseMusic,
    ResumeMusic,
}

/// Apply dirty Node2D properties to their registered Bevy entities.
fn sync_python_nodes(world: &mut World, py: Python<'_>) {
    let nodes: Vec<(u64, Entity, Py<PyAny>)> = {
        let runtime = world.resource::<PythonRuntime>();
        runtime
            .node_objects
            .iter()
            .filter_map(|(&node_id, object)| {
                let entity = runtime.nodes.get(&node_id).copied()?;
                Some((node_id, entity, object.clone_ref(py)))
            })
            .collect()
    };

    for (_node_id, entity, object) in nodes {
        let object = object.bind(py);
        let kind = object
            .getattr("_scrawl_node_kind")
            .and_then(|value| value.extract::<String>())
            .unwrap_or_default();
        let is_node2d = matches!(
            kind.as_str(),
            "node2d"
                | "static_body2d"
                | "rigid_body2d"
                | "kinematic_body2d"
                | "physics_body2d"
                | "collision_shape2d"
        );
        if !is_node2d {
            continue;
        }

        let dirty = object
            .call_method0("_take_node_dirty")
            .and_then(|value| value.extract::<bool>())
            .unwrap_or(true);
        if !dirty {
            continue;
        }

        let position = extract_python_vec2(object, "position", Vec2::ZERO);
        let scale = extract_python_vec2(object, "scale", Vec2::ONE);
        let rotation = object
            .getattr("rotation")
            .and_then(|value| value.extract::<f32>())
            .unwrap_or(0.0);
        let z_index = object
            .getattr("z_index")
            .and_then(|value| value.extract::<i32>())
            .unwrap_or(0);
        let visible = object
            .getattr("visible")
            .and_then(|value| value.extract::<bool>())
            .unwrap_or(true);

        if let Some(mut transform) = world.get_mut::<Transform>(entity) {
            transform.translation.x = position.x;
            transform.translation.y = position.y;
            transform.translation.z = z_index as f32;
            transform.rotation = Quat::from_rotation_z(rotation);
            transform.scale = Vec3::new(scale.x, scale.y, 1.0);
        }
        if let Some(mut node_visible) = world.get_mut::<Visible>(entity) {
            node_visible.0 = visible;
        }
        if let Some(mut visibility) = world.get_mut::<Visibility>(entity) {
            *visibility = if visible {
                Visibility::Inherited
            } else {
                Visibility::Hidden
            };
        }

        if matches!(
            kind.as_str(),
            "static_body2d" | "rigid_body2d" | "kinematic_body2d" | "physics_body2d"
        ) {
            let body_type = match kind.as_str() {
                "static_body2d" => PhysicsBodyType::Static,
                "kinematic_body2d" => PhysicsBodyType::Kinematic,
                _ => match object
                    .getattr("mode")
                    .and_then(|value| value.extract::<i32>())
                    .unwrap_or(0)
                {
                    1 => PhysicsBodyType::Static,
                    2 => PhysicsBodyType::Kinematic,
                    _ => PhysicsBodyType::Dynamic,
                },
            };
            if let Some(mut props) = world.get_mut::<PhysicsProps>(entity) {
                props.gravity_scale = object
                    .getattr("gravity_scale")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(props.gravity_scale);
                props.friction = object
                    .getattr("friction")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(props.friction);
                props.restitution = object
                    .getattr("bounce")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(props.restitution);
                props.body_type = body_type;
            }
            let velocity_attr = if kind == "kinematic_body2d" {
                "velocity"
            } else {
                "linear_velocity"
            };
            if let Some(mut velocity) = world.get_mut::<Velocity2D>(entity) {
                velocity.linear = extract_python_vec2(object, velocity_attr, velocity.linear);
                velocity.angular = object
                    .getattr("angular_velocity")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(velocity.angular);
            }
            if let Some(mut config) = world.get_mut::<PhysicsBodyConfig>(entity) {
                config.mass = object
                    .getattr("mass")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(config.mass);
                config.linear_damp = object
                    .getattr("linear_damp")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(config.linear_damp);
                config.angular_damp = object
                    .getattr("angular_damp")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(config.angular_damp);
                config.collision_layer = object
                    .getattr("collision_layer")
                    .and_then(|value| value.extract::<u32>())
                    .unwrap_or(config.collision_layer);
                config.collision_mask = object
                    .getattr("collision_mask")
                    .and_then(|value| value.extract::<u32>())
                    .unwrap_or(config.collision_mask);
                config.can_sleep = object
                    .getattr("can_sleep")
                    .and_then(|value| value.extract::<bool>())
                    .unwrap_or(config.can_sleep);
                config.sleeping = object
                    .getattr("sleeping")
                    .and_then(|value| value.extract::<bool>())
                    .unwrap_or(config.sleeping);
                config.freeze = object
                    .getattr("freeze")
                    .and_then(|value| value.extract::<bool>())
                    .unwrap_or(config.freeze);
            }
        } else if kind == "collision_shape2d" {
            if let Some(mut physics_shape) = world.get_mut::<PhysicsShape>(entity) {
                *physics_shape = extract_runtime_physics_shape(object);
            }
        }
    }
}

/// Copy Rapier-backed body state into Python after the physics writeback phase.
/// The Python helper writes private fields directly and clears its dirty bit,
/// so native simulation does not fight the regular Python-to-ECS sync.
fn sync_physics_nodes_to_python(world: &mut World) {
    let bodies: Vec<(Entity, Py<PyAny>)> = {
        let runtime = world.resource::<PythonRuntime>();
        runtime
            .node_objects
            .iter()
            .filter_map(|(node_id, object)| {
                let entity = runtime.nodes.get(node_id).copied()?;
                let kind = Python::with_gil(|py| {
                    object
                        .bind(py)
                        .getattr("_scrawl_node_kind")
                        .and_then(|value| value.extract::<String>())
                        .unwrap_or_default()
                });
                if matches!(
                    kind.as_str(),
                    "static_body2d" | "rigid_body2d" | "kinematic_body2d" | "physics_body2d"
                ) {
                    let object = Python::with_gil(|py| object.clone_ref(py));
                    Some((entity, object))
                } else {
                    None
                }
            })
            .collect()
    };

    Python::with_gil(|py| {
        for (entity, object) in bodies {
            let Some(transform) = world.get::<Transform2D>(entity).cloned() else {
                continue;
            };
            let velocity = world.get::<Velocity2D>(entity).cloned().unwrap_or_default();
            let _ = object.bind(py).call_method1(
                "_scrawl_sync_physics_state",
                (
                    transform.position.x,
                    transform.position.y,
                    transform.rotation_degrees,
                    velocity.linear.x,
                    velocity.linear.y,
                    velocity.angular,
                ),
            );
        }
    });
}

/// Spawn a Python node and all of its descendants after the game has started.
fn spawn_dynamic_subtree(
    world: &mut World,
    root: &Py<PyAny>,
    sprites: &mut Vec<PythonSpriteInstance>,
    parent_id: Option<u64>,
) {
    Python::with_gil(|py| {
        let root_bound = root.bind(py);
        let Ok(records) = root_bound.call_method0("_scrawl_tree_records") else {
            return;
        };
        let Ok(iter) = records.try_iter() else {
            return;
        };
        let records: Vec<(u64, Option<u64>, String, Py<PyAny>)> =
            iter.filter_map(|item| item.ok()?.extract().ok()).collect();

        for (node_id, record_parent_id, kind, object) in records {
            if world
                .resource::<PythonRuntime>()
                .nodes
                .contains_key(&node_id)
            {
                continue;
            }

            if kind == "sprite" {
                // Sprite creation already owns costume, handler, and collision setup.
                spawn_runtime_sprite(py, world, &object, sprites);
                continue;
            }

            let object_bound = object.bind(py);
            let name = object_bound
                .getattr("name")
                .and_then(|value| value.extract::<String>())
                .unwrap_or_else(|_| "Node".to_string());
            let entity = if kind == "node2d" {
                let position = extract_python_vec2(object_bound, "position", Vec2::ZERO);
                let scale = extract_python_vec2(object_bound, "scale", Vec2::ONE);
                let rotation = object_bound
                    .getattr("rotation")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(0.0);
                let z_index = object_bound
                    .getattr("z_index")
                    .and_then(|value| value.extract::<i32>())
                    .unwrap_or(0);
                let visible = object_bound
                    .getattr("visible")
                    .and_then(|value| value.extract::<bool>())
                    .unwrap_or(true);
                world
                    .spawn((
                        Transform::from_xyz(position.x, position.y, z_index as f32)
                            .with_rotation(Quat::from_rotation_z(rotation))
                            .with_scale(Vec3::new(scale.x, scale.y, 1.0)),
                        if visible {
                            Visibility::Inherited
                        } else {
                            Visibility::Hidden
                        },
                        ScrawlName(name),
                        ScrawlId::default(),
                        NodeType(NodeKind::Empty),
                        PythonNodeId(node_id),
                        Visible(visible),
                    ))
                    .id()
            } else if kind == "collision_shape2d" {
                let position = extract_python_vec2(object_bound, "position", Vec2::ZERO);
                let scale = extract_python_vec2(object_bound, "scale", Vec2::ONE);
                let rotation = object_bound
                    .getattr("rotation")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(0.0);
                let visible = object_bound
                    .getattr("visible")
                    .and_then(|value| value.extract::<bool>())
                    .unwrap_or(true);
                world
                    .spawn((
                        Transform::from_xyz(position.x, position.y, 0.0)
                            .with_rotation(Quat::from_rotation_z(rotation))
                            .with_scale(Vec3::new(scale.x, scale.y, 1.0)),
                        if visible {
                            Visibility::Inherited
                        } else {
                            Visibility::Hidden
                        },
                        ScrawlName(name),
                        ScrawlId::default(),
                        NodeType(NodeKind::Empty),
                        PythonNodeId(node_id),
                        Visible(visible),
                        extract_runtime_physics_shape(object_bound),
                    ))
                    .id()
            } else if matches!(
                kind.as_str(),
                "static_body2d" | "rigid_body2d" | "kinematic_body2d" | "physics_body2d"
            ) {
                let position = extract_python_vec2(object_bound, "position", Vec2::ZERO);
                let scale = extract_python_vec2(object_bound, "scale", Vec2::ONE);
                let rotation = object_bound
                    .getattr("rotation")
                    .and_then(|value| value.extract::<f32>())
                    .unwrap_or(0.0);
                let z_index = object_bound
                    .getattr("z_index")
                    .and_then(|value| value.extract::<i32>())
                    .unwrap_or(0);
                let visible = object_bound
                    .getattr("visible")
                    .and_then(|value| value.extract::<bool>())
                    .unwrap_or(true);
                let body_type = runtime_physics_body_type(object_bound, &kind);
                let velocity_attr = if kind == "kinematic_body2d" {
                    "velocity"
                } else {
                    "linear_velocity"
                };
                let props = PhysicsProps {
                    gravity_scale: object_bound
                        .getattr("gravity_scale")
                        .and_then(|value| value.extract::<f32>())
                        .unwrap_or(1.0),
                    friction: object_bound
                        .getattr("friction")
                        .and_then(|value| value.extract::<f32>())
                        .unwrap_or(0.02),
                    restitution: object_bound
                        .getattr("bounce")
                        .and_then(|value| value.extract::<f32>())
                        .unwrap_or(0.0),
                    body_type,
                };
                let config = PhysicsBodyConfig {
                    mass: object_bound
                        .getattr("mass")
                        .and_then(|value| value.extract::<f32>())
                        .unwrap_or(1.0),
                    linear_damp: object_bound
                        .getattr("linear_damp")
                        .and_then(|value| value.extract::<f32>())
                        .unwrap_or(0.0),
                    angular_damp: object_bound
                        .getattr("angular_damp")
                        .and_then(|value| value.extract::<f32>())
                        .unwrap_or(0.0),
                    collision_layer: object_bound
                        .getattr("collision_layer")
                        .and_then(|value| value.extract::<u32>())
                        .unwrap_or(1),
                    collision_mask: object_bound
                        .getattr("collision_mask")
                        .and_then(|value| value.extract::<u32>())
                        .unwrap_or(1),
                    can_sleep: object_bound
                        .getattr("can_sleep")
                        .and_then(|value| value.extract::<bool>())
                        .unwrap_or(true),
                    sleeping: object_bound
                        .getattr("sleeping")
                        .and_then(|value| value.extract::<bool>())
                        .unwrap_or(false),
                    freeze: object_bound
                        .getattr("freeze")
                        .and_then(|value| value.extract::<bool>())
                        .unwrap_or(false),
                };
                let velocity = Velocity2D {
                    linear: extract_python_vec2(object_bound, velocity_attr, Vec2::ZERO),
                    angular: object_bound
                        .getattr("angular_velocity")
                        .and_then(|value| value.extract::<f32>())
                        .unwrap_or(0.0),
                };
                world
                    .spawn((
                        Transform::from_xyz(position.x, position.y, z_index as f32)
                            .with_rotation(Quat::from_rotation_z(rotation))
                            .with_scale(Vec3::new(scale.x, scale.y, 1.0)),
                        if visible {
                            Visibility::Inherited
                        } else {
                            Visibility::Hidden
                        },
                        ScrawlName(name),
                        ScrawlId::default(),
                        NodeType(NodeKind::PhysicsBody),
                        PythonNodeId(node_id),
                        Visible(visible),
                        Transform2D {
                            position,
                            rotation_degrees: 90.0 - rotation.to_degrees(),
                            scale,
                        },
                        props,
                        config,
                        velocity,
                    ))
                    .id()
            } else {
                world
                    .spawn((
                        Transform::default(),
                        ScrawlName(name),
                        ScrawlId::default(),
                        NodeType(NodeKind::Empty),
                        PythonNodeId(node_id),
                    ))
                    .id()
            };

            world
                .resource_mut::<PythonRuntime>()
                .nodes
                .insert(node_id, entity);
            world
                .resource_mut::<PythonRuntime>()
                .node_objects
                .insert(node_id, object.clone_ref(py));
            let _ = object_bound.call_method0("_take_node_dirty");

            let effective_parent_id = record_parent_id.or(parent_id);
            if let Some(parent_entity) = effective_parent_id
                .and_then(|id| world.resource::<PythonRuntime>().nodes.get(&id).copied())
            {
                world.entity_mut(entity).set_parent(parent_entity);
            }
        }
    });
}

fn reparent_python_node(world: &mut World, node_id: u64, parent_id: u64) {
    let Some(entity) = world
        .resource::<PythonRuntime>()
        .nodes
        .get(&node_id)
        .copied()
    else {
        return;
    };
    let Some(parent_entity) = world
        .resource::<PythonRuntime>()
        .nodes
        .get(&parent_id)
        .copied()
    else {
        return;
    };
    if entity != parent_entity {
        world.entity_mut(entity).set_parent(parent_entity);
    }
}

fn despawn_python_subtree(
    world: &mut World,
    root_id: u64,
    root: &Py<PyAny>,
    sprites: &mut Vec<PythonSpriteInstance>,
) {
    let mut node_ids = Python::with_gil(|py| {
        root.bind(py)
            .call_method0("_scrawl_tree_records")
            .ok()
            .and_then(|records| records.try_iter().ok())
            .map(|iter| {
                iter.filter_map(|item| {
                    item.ok()?
                        .extract::<(u64, Option<u64>, String, Py<PyAny>)>()
                        .ok()
                        .map(|record| record.0)
                })
                .collect::<Vec<_>>()
            })
            .unwrap_or_else(|| vec![root_id])
    });
    if !node_ids.contains(&root_id) {
        node_ids.push(root_id);
    }

    let node_id_set: HashSet<u64> = node_ids.iter().copied().collect();
    let root_entity = world
        .resource::<PythonRuntime>()
        .nodes
        .get(&root_id)
        .copied();
    let sprite_ptrs: Vec<usize> = Python::with_gil(|py| {
        sprites
            .iter()
            .filter(|sprite| node_id_set.contains(&sprite.node_id))
            .map(|sprite| sprite.py_object.bind(py).as_ptr() as usize)
            .collect()
    });
    for ptr_id in sprite_ptrs {
        despawn_text_displays_for_owner(world, ptr_id);
    }

    sprites.retain(|sprite| !node_id_set.contains(&sprite.node_id));
    {
        let mut runtime = world.resource_mut::<PythonRuntime>();
        for node_id in &node_ids {
            runtime.nodes.remove(node_id);
            runtime.node_objects.remove(node_id);
        }
    }

    if let Some(entity) = root_entity {
        if world.get_entity(entity).is_ok() {
            world.entity_mut(entity).despawn_recursive();
        }
    }
}

fn extract_python_vec2(object: &Bound<'_, PyAny>, attr: &str, fallback: Vec2) -> Vec2 {
    let Ok(value) = object.getattr(attr) else {
        return fallback;
    };
    let x = value
        .getattr("x")
        .and_then(|component| component.extract::<f32>());
    let y = value
        .getattr("y")
        .and_then(|component| component.extract::<f32>());
    match (x, y) {
        (Ok(x), Ok(y)) => Vec2::new(x, y),
        _ => fallback,
    }
}

fn extract_runtime_physics_shape(object: &Bound<'_, PyAny>) -> PhysicsShape {
    let disabled = object
        .getattr("disabled")
        .and_then(|value| value.extract::<bool>())
        .unwrap_or(false);
    let Some(shape) = object.getattr("shape").ok() else {
        return PhysicsShape {
            disabled,
            ..default()
        };
    };
    let class_name = shape
        .getattr("__class__")
        .and_then(|class| class.getattr("__name__"))
        .and_then(|name| name.extract::<String>())
        .unwrap_or_default();
    match class_name.as_str() {
        "CircleShape2D" => PhysicsShape {
            kind: CollisionKind::Circle,
            size: None,
            radius: shape
                .getattr("radius")
                .and_then(|value| value.extract::<f32>())
                .ok(),
            disabled,
        },
        "RectangleShape2D" => PhysicsShape {
            kind: CollisionKind::Rect,
            size: Some(extract_python_vec2(&shape, "size", Vec2::new(32.0, 32.0))),
            radius: None,
            disabled,
        },
        _ => PhysicsShape {
            kind: CollisionKind::Rect,
            size: Some(Vec2::new(32.0, 32.0)),
            radius: None,
            disabled,
        },
    }
}

fn runtime_physics_body_type(object: &Bound<'_, PyAny>, kind: &str) -> PhysicsBodyType {
    match kind {
        "static_body2d" => PhysicsBodyType::Static,
        "kinematic_body2d" => PhysicsBodyType::Kinematic,
        "rigid_body2d" => match object
            .getattr("mode")
            .and_then(|value| value.extract::<i32>())
            .unwrap_or(0)
        {
            1 => PhysicsBodyType::Static,
            2 => PhysicsBodyType::Kinematic,
            _ => PhysicsBodyType::Dynamic,
        },
        _ => PhysicsBodyType::Dynamic,
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum TextDisplayKind {
    Persistent,
    Speech,
}

/// Marker for text entities spawned by set_text().
#[derive(Component)]
struct ScrawlTextDisplay {
    owner_ptr: usize,
    kind: TextDisplayKind,
    expires_at: Option<Instant>,
    y_offset: f32,
}

/// Read and drain the Python-side _scrawl_command_queue.
fn process_python_commands(py: Python<'_>) -> Vec<PythonCommand> {
    let mut commands = Vec::new();

    let module = match py.import("scrawl.node") {
        Ok(m) => m,
        Err(_) => return commands,
    };

    let queue = match module.getattr("_scrawl_command_queue") {
        Ok(q) => q,
        Err(_) => return commands,
    };

    let items: Vec<pyo3::Bound<'_, PyAny>> = match queue.try_iter() {
        Ok(iter) => iter.filter_map(|i| i.ok()).collect(),
        Err(_) => return commands,
    };

    for item in &items {
        if let Ok(tuple) = item.downcast::<pyo3::types::PyTuple>() {
            if tuple.is_empty() {
                continue;
            }
            let cmd_type: String = match tuple.get_item(0).and_then(|v| v.extract()) {
                Ok(s) => s,
                Err(_) => continue,
            };
            match cmd_type.as_str() {
                "node_add" => {
                    if tuple.len() >= 3 {
                        let Ok(node_obj) = tuple.get_item(1) else {
                            continue;
                        };
                        let Ok(parent_obj) = tuple.get_item(2) else {
                            continue;
                        };
                        let parent_id = parent_obj
                            .getattr("_scrawl_node_id")
                            .and_then(|value| value.extract::<u64>())
                            .ok();
                        commands.push(PythonCommand::NodeAdd {
                            node: node_obj.unbind(),
                            parent_id,
                        });
                    }
                }
                "node_remove" => {
                    if tuple.len() >= 2 {
                        let Ok(node_obj) = tuple.get_item(1) else {
                            continue;
                        };
                        let Ok(node_id) = node_obj
                            .getattr("_scrawl_node_id")
                            .and_then(|value| value.extract::<u64>())
                        else {
                            continue;
                        };
                        commands.push(PythonCommand::NodeRemove {
                            node_id,
                            node: node_obj.unbind(),
                        });
                    }
                }
                "node_reparent" => {
                    if tuple.len() >= 3 {
                        let Ok(node_obj) = tuple.get_item(1) else {
                            continue;
                        };
                        let Ok(parent_obj) = tuple.get_item(2) else {
                            continue;
                        };
                        let Ok(node_id) = node_obj
                            .getattr("_scrawl_node_id")
                            .and_then(|value| value.extract::<u64>())
                        else {
                            continue;
                        };
                        let Ok(parent_id) = parent_obj
                            .getattr("_scrawl_node_id")
                            .and_then(|value| value.extract::<u64>())
                        else {
                            continue;
                        };
                        commands.push(PythonCommand::NodeReparent { node_id, parent_id });
                    }
                }
                "broadcast" => {
                    if let Ok(event) = tuple.get_item(1).and_then(|v| v.extract::<String>()) {
                        commands.push(PythonCommand::Broadcast(event));
                    }
                }
                "text" => {
                    // ("text", sprite_obj, text_str, font_size, (r, g, b))
                    if tuple.len() >= 5 {
                        if let Ok(sprite_obj) = tuple.get_item(1) {
                            let ptr_id = sprite_obj.as_ptr() as usize;
                            let text = tuple
                                .get_item(2)
                                .and_then(|v| v.extract::<String>())
                                .unwrap_or_default();
                            let font_size = tuple
                                .get_item(3)
                                .and_then(|v| v.extract::<f32>())
                                .unwrap_or(20.0);
                            let color = if let Ok(c) = tuple.get_item(4) {
                                if let Ok((r, g, b)) = c.extract::<(u8, u8, u8)>() {
                                    [r as f32 / 255.0, g as f32 / 255.0, b as f32 / 255.0]
                                } else {
                                    [1.0, 1.0, 1.0]
                                }
                            } else {
                                [1.0, 1.0, 1.0]
                            };
                            commands.push(PythonCommand::SetText {
                                ptr_id,
                                text,
                                font_size,
                                color,
                            });
                        }
                    }
                }
                "say" => {
                    // ("say", sprite_obj, text_str, duration_ms)
                    if tuple.len() >= 4 {
                        if let Ok(sprite_obj) = tuple.get_item(1) {
                            let ptr_id = sprite_obj.as_ptr() as usize;
                            let text = tuple
                                .get_item(2)
                                .and_then(|v| v.extract::<String>())
                                .unwrap_or_default();
                            let duration_ms = tuple
                                .get_item(3)
                                .and_then(|v| v.extract::<u64>())
                                .unwrap_or(2000);
                            commands.push(PythonCommand::Say {
                                ptr_id,
                                text,
                                duration_ms,
                            });
                        }
                    }
                }
                "play_sound" => {
                    if tuple.len() >= 2 {
                        let path = tuple
                            .get_item(1)
                            .and_then(|v| v.extract::<String>())
                            .unwrap_or_default();
                        let volume = if tuple.len() >= 3 {
                            tuple.get_item(2).and_then(|v| v.extract::<f64>()).ok()
                        } else {
                            None
                        };
                        if !path.is_empty() {
                            commands.push(PythonCommand::PlaySound { path, volume });
                        }
                    }
                }
                "play_music" => {
                    if tuple.len() >= 3 {
                        let path = tuple
                            .get_item(1)
                            .and_then(|v| v.extract::<String>())
                            .unwrap_or_default();
                        let loops = tuple
                            .get_item(2)
                            .and_then(|v| v.extract::<i32>())
                            .unwrap_or(-1);
                        let volume = if tuple.len() >= 4 {
                            tuple.get_item(3).and_then(|v| v.extract::<f64>()).ok()
                        } else {
                            None
                        };
                        if !path.is_empty() {
                            commands.push(PythonCommand::PlayMusic {
                                path,
                                loops,
                                volume,
                            });
                        }
                    }
                }
                "stop_music" => commands.push(PythonCommand::StopMusic),
                "pause_music" => commands.push(PythonCommand::PauseMusic),
                "resume_music" => commands.push(PythonCommand::ResumeMusic),
                _ => {}
            }
        }
    }

    // Clear the queue
    let _ = queue.call_method0("clear");

    commands
}

/// Start a Python handler method as a coroutine.
fn start_handler(
    py: Python<'_>,
    sprite: &mut PythonSpriteInstance,
    method_name: &str,
    coro_key: String,
) {
    if let Ok(gen) = sprite.py_object.bind(py).call_method0(method_name) {
        if gen.hasattr("__next__").unwrap_or(false) {
            sprite.coroutines.insert(coro_key, gen.unbind());
        }
    }
}

fn mouse_button_number(button: MouseButton) -> Option<u32> {
    match button {
        MouseButton::Left => Some(1),
        MouseButton::Middle => Some(2),
        MouseButton::Right => Some(3),
        _ => None,
    }
}

fn synthesize_sprite_clicked_entities(
    world: &mut World,
    mouse_events: &[MouseInputEvent],
) -> HashSet<Entity> {
    let mut clicked = HashSet::new();

    for event in mouse_events {
        if event.button != MouseButton::Left || event.mode != InputMode::Pressed {
            continue;
        }

        let Some(world_pos) = screen_to_world_position(world, event.position) else {
            continue;
        };

        let mut sprite_query = world.query::<(
            Entity,
            &Transform2D,
            Option<&bevy::sprite::Sprite>,
            Option<&CollisionShape>,
            Option<&CollisionMask>,
            &Visible,
            &NodeType,
        )>();

        for (entity, t2d, sprite, shape, mask, visible, node_type) in sprite_query.iter(world) {
            if !visible.0 || node_type.0 != NodeKind::Sprite {
                continue;
            }

            if point_hits_sprite(world_pos, t2d, sprite, shape, mask) {
                clicked.insert(entity);
            }
        }
    }

    clicked
}

fn screen_to_world_position(world: &mut World, screen_pos: Vec2) -> Option<Vec2> {
    let mut camera_query = world.query::<(&Camera, &GlobalTransform)>();
    let (camera, camera_transform) = camera_query.iter(world).next()?;
    camera
        .viewport_to_world_2d(camera_transform, screen_pos)
        .ok()
}

fn point_hits_sprite(
    world_pos: Vec2,
    t2d: &Transform2D,
    sprite: Option<&bevy::sprite::Sprite>,
    shape: Option<&CollisionShape>,
    mask: Option<&CollisionMask>,
) -> bool {
    let shape = shape.cloned().unwrap_or_default();

    match shape.kind {
        CollisionKind::Circle => {
            let radius = click_circle_radius(t2d, &shape, sprite, mask);
            t2d.position.distance(world_pos) <= radius
        }
        CollisionKind::Rect => {
            let half = click_half_size(t2d, sprite, mask);
            let local = click_local_point(world_pos, t2d);
            local.x.abs() <= half.x && local.y.abs() <= half.y
        }
        CollisionKind::Mask => {
            let local = click_local_point(world_pos, t2d);
            let half = click_half_size(t2d, sprite, mask);

            if local.x.abs() > half.x || local.y.abs() > half.y {
                return false;
            }

            let Some(mask) = mask else {
                return true;
            };

            let base = click_base_size(sprite, Some(mask));
            let scale = Vec2::new(
                t2d.scale.x.abs().max(f32::EPSILON),
                t2d.scale.y.abs().max(f32::EPSILON),
            );

            let pixel_x = ((local.x / scale.x) + base.x / 2.0).floor() as i32;
            let pixel_y = ((local.y / scale.y) + base.y / 2.0).floor() as i32;
            mask.is_solid(pixel_x, pixel_y)
        }
    }
}

fn click_local_point(world_pos: Vec2, t2d: &Transform2D) -> Vec2 {
    let delta = world_pos - t2d.position;
    let rad = (t2d.rotation_degrees - 90.0).to_radians();
    let cos = rad.cos();
    let sin = rad.sin();

    Vec2::new(delta.x * cos - delta.y * sin, delta.x * sin + delta.y * cos)
}

fn click_half_size(
    t2d: &Transform2D,
    sprite: Option<&bevy::sprite::Sprite>,
    mask: Option<&CollisionMask>,
) -> Vec2 {
    let base = click_base_size(sprite, mask);

    Vec2::new(base.x * t2d.scale.x.abs(), base.y * t2d.scale.y.abs()) / 2.0
}

fn click_base_size(sprite: Option<&bevy::sprite::Sprite>, mask: Option<&CollisionMask>) -> Vec2 {
    sprite
        .and_then(|value| value.custom_size)
        .or_else(|| mask.map(|value| Vec2::new(value.width as f32, value.height as f32)))
        .unwrap_or(Vec2::new(50.0, 50.0))
}

fn click_circle_radius(
    t2d: &Transform2D,
    shape: &CollisionShape,
    sprite: Option<&bevy::sprite::Sprite>,
    mask: Option<&CollisionMask>,
) -> f32 {
    if let Some(radius) = shape.radius {
        radius * t2d.scale.x.abs().max(t2d.scale.y.abs())
    } else {
        let half = click_half_size(t2d, sprite, mask);
        half.x.max(half.y)
    }
}

fn play_sound_command(world: &mut World, path: &str, volume: Option<f64>) {
    world.resource_scope(|world, mut audio_manager: Mut<AudioManager>| {
        let audio = world.resource::<Audio>();
        let asset_server = world.resource::<AssetServer>();

        let previous_volume = audio_manager.sound_volume;
        if let Some(value) = volume {
            audio_manager.set_sound_volume(value);
        }
        audio_manager.play_sound(audio, asset_server, path);
        if volume.is_some() {
            audio_manager.set_sound_volume(previous_volume);
        }
    });
}

fn play_music_command(world: &mut World, path: &str, _loops: i32, volume: Option<f64>) {
    world.resource_scope(|world, mut audio_manager: Mut<AudioManager>| {
        let audio = world.resource::<Audio>();
        let asset_server = world.resource::<AssetServer>();
        let looped = _loops < 0;

        let previous_volume = audio_manager.music_volume;
        if let Some(value) = volume {
            audio_manager.set_music_volume(value);
        }
        audio_manager.play_music(audio, asset_server, looped, path);
        if volume.is_some() {
            audio_manager.set_music_volume(previous_volume);
        }
    });
}

fn stop_music_command(world: &mut World) {
    world.resource_scope(|world, mut audio_manager: Mut<AudioManager>| {
        let mut audio_instances = world.resource_mut::<Assets<bevy_kira_audio::AudioInstance>>();
        audio_manager.stop_music(&mut audio_instances);
    });
}

fn pause_music_command(world: &mut World) {
    world.resource_scope(|world, audio_manager: Mut<AudioManager>| {
        let mut audio_instances = world.resource_mut::<Assets<bevy_kira_audio::AudioInstance>>();
        audio_manager.pause_music(&mut audio_instances);
    });
}

fn resume_music_command(world: &mut World) {
    world.resource_scope(|world, audio_manager: Mut<AudioManager>| {
        let mut audio_instances = world.resource_mut::<Assets<bevy_kira_audio::AudioInstance>>();
        audio_manager.resume_music(&mut audio_instances);
    });
}

fn sprite_position_for_ptr(world: &World, sprites: &[PythonSpriteInstance], ptr_id: usize) -> Vec2 {
    let sprite = sprites.iter().find(|sprite| {
        Python::with_gil(|py| sprite.py_object.bind(py).as_ptr() as usize == ptr_id)
    });
    let Some(sprite) = sprite else {
        return Vec2::new(400.0, 300.0);
    };

    if let Some(global) = world.get::<GlobalTransform>(sprite.entity) {
        return global.translation().truncate();
    }

    Python::with_gil(|py| {
        let obj = sprite.py_object.bind(py);
        let x = obj
            .getattr("x")
            .and_then(|v| v.extract::<f32>())
            .unwrap_or(400.0);
        let y = obj
            .getattr("y")
            .and_then(|v| v.extract::<f32>())
            .unwrap_or(300.0);
        Vec2::new(x, y)
    })
}

fn sync_pen_state_from_python(
    world: &mut World,
    entity: Entity,
    obj: &Bound<'_, PyAny>,
    previous_position: Option<Vec2>,
) {
    let current_position = world
        .get::<Transform2D>(entity)
        .map(|transform| transform.position)
        .or(previous_position);

    let pen_down = obj
        .getattr("_pen_down")
        .and_then(|value| value.extract::<bool>())
        .unwrap_or(false);

    let pen_color = obj
        .getattr("_pen_color")
        .and_then(|value| value.extract::<(u8, u8, u8)>())
        .map(|(r, g, b)| Color::srgb(r as f32 / 255.0, g as f32 / 255.0, b as f32 / 255.0))
        .unwrap_or(Color::BLACK);

    let pen_size = obj
        .getattr("_pen_size")
        .and_then(|value| value.extract::<f32>())
        .unwrap_or(2.0);

    let Some(mut pen) = world.get_mut::<PenState>(entity) else {
        return;
    };

    pen.down = pen_down;
    pen.color = pen_color;
    pen.size = pen_size;

    let (Some(from), Some(to)) = (previous_position, current_position) else {
        return;
    };

    if !pen.down || from.distance_squared(to) <= f32::EPSILON {
        return;
    }

    if pen.path.last().copied() != Some(from) {
        pen.path.push(from);
    }
    pen.path.push(to);
}

fn find_text_display_entity(
    world: &mut World,
    ptr_id: usize,
    kind: TextDisplayKind,
) -> Option<Entity> {
    let mut text_query = world.query::<(Entity, &ScrawlTextDisplay)>();
    for (entity, display) in text_query.iter(world) {
        if display.owner_ptr == ptr_id && display.kind == kind {
            return Some(entity);
        }
    }
    None
}

fn despawn_text_displays_for_owner(world: &mut World, ptr_id: usize) {
    let mut to_despawn = Vec::new();

    {
        let mut text_query = world.query::<(Entity, &ScrawlTextDisplay)>();
        for (entity, display) in text_query.iter(world) {
            if display.owner_ptr == ptr_id {
                to_despawn.push(entity);
            }
        }
    }

    for entity in to_despawn {
        world.despawn(entity);
    }
}

fn upsert_text_display(
    world: &mut World,
    sprites: &[PythonSpriteInstance],
    ptr_id: usize,
    kind: TextDisplayKind,
    text: String,
    font_size: f32,
    color: [f32; 3],
    y_offset: f32,
    expires_at: Option<Instant>,
) {
    let existing = find_text_display_entity(world, ptr_id, kind);

    if text.is_empty() {
        if let Some(entity) = existing {
            world.despawn(entity);
        }
        return;
    }

    let sprite_pos = sprite_position_for_ptr(world, sprites, ptr_id);

    if let Some(entity) = existing {
        if let Some(mut text_value) = world.get_mut::<Text2d>(entity) {
            **text_value = text;
        }
        if let Some(mut text_font) = world.get_mut::<TextFont>(entity) {
            text_font.font_size = font_size;
        }
        if let Some(mut text_color) = world.get_mut::<TextColor>(entity) {
            text_color.0 = Color::srgb(color[0], color[1], color[2]);
        }
        if let Some(mut transform) = world.get_mut::<Transform>(entity) {
            transform.translation.x = sprite_pos.x;
            transform.translation.y = sprite_pos.y + y_offset;
        }
        if let Some(mut display) = world.get_mut::<ScrawlTextDisplay>(entity) {
            display.expires_at = expires_at;
            display.y_offset = y_offset;
        }
        return;
    }

    world.spawn((
        ScrawlTextDisplay {
            owner_ptr: ptr_id,
            kind,
            expires_at,
            y_offset,
        },
        Text2d::new(text),
        TextFont {
            font_size,
            ..default()
        },
        TextColor(Color::srgb(color[0], color[1], color[2])),
        Transform::from_xyz(sprite_pos.x, sprite_pos.y + y_offset, 500.0),
    ));
}

fn sync_text_displays(world: &mut World, sprites: &[PythonSpriteInstance]) {
    let now = Instant::now();
    let mut to_despawn = Vec::new();
    let mut updates = Vec::new();

    {
        let mut text_query = world.query::<(Entity, &ScrawlTextDisplay)>();
        for (entity, display) in text_query.iter(world) {
            if display.expires_at.is_some_and(|deadline| deadline <= now) {
                to_despawn.push(entity);
                continue;
            }

            let sprite_pos = sprite_position_for_ptr(world, sprites, display.owner_ptr);
            updates.push((entity, sprite_pos.x, sprite_pos.y + display.y_offset));
        }
    }

    for entity in to_despawn {
        world.despawn(entity);
    }

    for (entity, x, y) in updates {
        if let Some(mut transform) = world.get_mut::<Transform>(entity) {
            transform.translation.x = x;
            transform.translation.y = y;
        }
    }
}

/// Spawn a Sprite entity after the game has started.
fn spawn_runtime_sprite(
    py: Python<'_>,
    world: &mut World,
    py_sprite: &Py<PyAny>,
    sprites: &mut Vec<PythonSpriteInstance>,
) {
    let obj = py_sprite.bind(py);

    let node_id = obj
        .getattr("_scrawl_node_id")
        .and_then(|v| v.extract::<u64>())
        .unwrap_or(0);
    let name = obj
        .getattr("name")
        .and_then(|v| v.extract::<String>())
        .unwrap_or_else(|_| "Clone".into());
    let x = obj
        .getattr("x")
        .and_then(|v| v.extract::<f32>())
        .unwrap_or(400.0);
    let y = obj
        .getattr("y")
        .and_then(|v| v.extract::<f32>())
        .unwrap_or(300.0);
    let dir = obj
        .getattr("direction")
        .and_then(|v| v.extract::<f32>())
        .unwrap_or(90.0);
    let size = obj
        .getattr("size")
        .and_then(|v| v.extract::<f32>())
        .unwrap_or(1.0);
    let width = obj
        .getattr("width")
        .ok()
        .and_then(|v| v.extract::<Option<f32>>().ok())
        .flatten();
    let height = obj
        .getattr("height")
        .ok()
        .and_then(|v| v.extract::<Option<f32>>().ok())
        .flatten();
    let z_index = obj
        .getattr("z_index")
        .and_then(|v| v.extract::<i32>())
        .unwrap_or(0);
    let visible = obj
        .getattr("visible")
        .and_then(|v| v.extract::<bool>())
        .unwrap_or(true);
    let is_clone = obj
        .getattr("is_clones")
        .and_then(|value| value.extract::<bool>())
        .unwrap_or(false);
    let collision_type = obj
        .getattr("collision_type")
        .and_then(|v| v.extract::<String>())
        .unwrap_or_else(|_| "rect".into());

    let color = if let Ok(c) = obj.getattr("color") {
        if let Ok((r, g, b)) = c.extract::<(u8, u8, u8)>() {
            Color::srgb(r as f32 / 255.0, g as f32 / 255.0, b as f32 / 255.0)
        } else {
            Color::srgb(1.0, 0.4, 0.4)
        }
    } else {
        Color::srgb(1.0, 0.4, 0.4)
    };

    let collision_kind = match collision_type.as_str() {
        "circle" => CollisionKind::Circle,
        "mask" => CollisionKind::Mask,
        _ => CollisionKind::Rect,
    };

    // Load costume if available
    let costumes_dict = obj.getattr("_costumes").ok();
    let mut costume_set = CostumeSet::default();
    let mut first_image: Option<Handle<Image>> = None;

    if let Some(dict_obj) = costumes_dict {
        if let Ok(dict) = dict_obj.downcast::<pyo3::types::PyDict>() {
            let asset_server = world.resource::<AssetServer>();
            for (k, v) in dict.iter() {
                if let (Ok(cname), Ok(cpath)) = (k.extract::<String>(), v.extract::<String>()) {
                    let handle: Handle<Image> = asset_server.load(cpath.clone());
                    if first_image.is_none() {
                        first_image = Some(handle.clone());
                    }
                    costume_set.costumes.push(CostumeEntry {
                        name: cname,
                        path: cpath,
                        handle: Some(handle),
                    });
                }
            }
        }
    }

    let custom_size = custom_sprite_size(width, height, first_image.is_some());
    let bevy_sprite = if let Some(ref img) = first_image {
        Sprite {
            image: img.clone(),
            color: Color::WHITE,
            custom_size,
            ..default()
        }
    } else {
        Sprite {
            color,
            custom_size,
            ..default()
        }
    };

    let entity = world
        .spawn((
            bevy_sprite,
            Transform::from_xyz(x, y, z_index as f32).with_scale(Vec3::splat(size)),
            ScrawlName(name.clone()),
            ScrawlId::default(),
            Transform2D {
                position: Vec2::new(x, y),
                rotation_degrees: dir,
                scale: Vec2::splat(size),
            },
            Visible(visible),
            SpriteColor(if first_image.is_some() {
                Color::WHITE
            } else {
                color
            }),
            CollisionShape {
                kind: collision_kind,
                radius: None,
            },
            PenState::default(),
            NodeType(NodeKind::Sprite),
            PythonNodeId(node_id),
            costume_set,
        ))
        .id();
    if is_clone {
        world.entity_mut(entity).insert(IsClone);
    }

    let parent_id = obj
        .getattr("_parent")
        .ok()
        .filter(|parent| !parent.is_none())
        .and_then(|parent| parent.getattr("_scrawl_node_id").ok())
        .and_then(|value| value.extract::<u64>().ok());
    if let Some(parent_entity) =
        parent_id.and_then(|id| world.resource::<PythonRuntime>().nodes.get(&id).copied())
    {
        world.entity_mut(entity).set_parent(parent_entity);
    }
    world
        .resource_mut::<PythonRuntime>()
        .nodes
        .insert(node_id, entity);
    world
        .resource_mut::<PythonRuntime>()
        .node_objects
        .insert(node_id, py_sprite.clone_ref(py));

    // New regular sprites start @as_main; clones start @as_clones.
    let handlers = scan_python_handlers(py, &obj);
    let mut coroutines = HashMap::new();
    let wake_times = HashMap::new();

    for (method_name, kind) in &handlers {
        let should_start = if is_clone {
            matches!(kind, HandlerKind::Clone)
        } else {
            matches!(kind, HandlerKind::Main)
        };
        if should_start {
            if let Ok(gen) = obj.call_method0(method_name.as_str()) {
                if gen.hasattr("__next__").unwrap_or(false) {
                    let prefix = if is_clone { "clone" } else { "main" };
                    coroutines.insert(format!("{}_{}", prefix, method_name), gen.unbind());
                }
            }
        }
    }

    // Set scene reference on the Python sprite
    // (so face_towards etc. can find other sprites)
    // obj is the new clone's Python object

    let _ = obj.call_method0("_take_dirty");
    sprites.push(PythonSpriteInstance {
        node_id,
        py_object: py_sprite.clone_ref(py),
        entity,
        coroutines,
        wake_times,
        handlers,
    });
}

fn custom_sprite_size(width: Option<f32>, height: Option<f32>, has_image: bool) -> Option<Vec2> {
    match (width, height, has_image) {
        (None, None, true) => None,
        (width, height, _) => Some(Vec2::new(width.unwrap_or(40.0), height.unwrap_or(40.0))),
    }
}

/// Convert a Bevy KeyCode to the string format used by scrawl Python API.
fn format_key_code(key: KeyCode) -> String {
    match key {
        KeyCode::Space => "space".into(),
        KeyCode::Enter => "return".into(),
        KeyCode::Escape => "escape".into(),
        KeyCode::Backspace => "backspace".into(),
        KeyCode::Tab => "tab".into(),
        KeyCode::ArrowLeft => "left".into(),
        KeyCode::ArrowRight => "right".into(),
        KeyCode::ArrowUp => "up".into(),
        KeyCode::ArrowDown => "down".into(),
        KeyCode::ShiftLeft => "lshift".into(),
        KeyCode::ShiftRight => "rshift".into(),
        KeyCode::ControlLeft => "lctrl".into(),
        KeyCode::ControlRight => "rctrl".into(),
        KeyCode::AltLeft => "lalt".into(),
        KeyCode::AltRight => "ralt".into(),
        KeyCode::KeyA => "a".into(),
        KeyCode::KeyB => "b".into(),
        KeyCode::KeyC => "c".into(),
        KeyCode::KeyD => "d".into(),
        KeyCode::KeyE => "e".into(),
        KeyCode::KeyF => "f".into(),
        KeyCode::KeyG => "g".into(),
        KeyCode::KeyH => "h".into(),
        KeyCode::KeyI => "i".into(),
        KeyCode::KeyJ => "j".into(),
        KeyCode::KeyK => "k".into(),
        KeyCode::KeyL => "l".into(),
        KeyCode::KeyM => "m".into(),
        KeyCode::KeyN => "n".into(),
        KeyCode::KeyO => "o".into(),
        KeyCode::KeyP => "p".into(),
        KeyCode::KeyQ => "q".into(),
        KeyCode::KeyR => "r".into(),
        KeyCode::KeyS => "s".into(),
        KeyCode::KeyT => "t".into(),
        KeyCode::KeyU => "u".into(),
        KeyCode::KeyV => "v".into(),
        KeyCode::KeyW => "w".into(),
        KeyCode::KeyX => "x".into(),
        KeyCode::KeyY => "y".into(),
        KeyCode::KeyZ => "z".into(),
        KeyCode::Digit0 => "0".into(),
        KeyCode::Digit1 => "1".into(),
        KeyCode::Digit2 => "2".into(),
        KeyCode::Digit3 => "3".into(),
        KeyCode::Digit4 => "4".into(),
        KeyCode::Digit5 => "5".into(),
        KeyCode::Digit6 => "6".into(),
        KeyCode::Digit7 => "7".into(),
        KeyCode::Digit8 => "8".into(),
        KeyCode::Digit9 => "9".into(),
        KeyCode::F1 => "f1".into(),
        KeyCode::F2 => "f2".into(),
        KeyCode::F3 => "f3".into(),
        KeyCode::F4 => "f4".into(),
        KeyCode::F5 => "f5".into(),
        KeyCode::F6 => "f6".into(),
        KeyCode::F7 => "f7".into(),
        KeyCode::F8 => "f8".into(),
        KeyCode::F9 => "f9".into(),
        KeyCode::F10 => "f10".into(),
        KeyCode::F11 => "f11".into(),
        KeyCode::F12 => "f12".into(),
        other => format!("{:?}", other).to_lowercase(),
    }
}

/// Scan a Python sprite instance for decorated handlers and return their info.
pub fn scan_python_handlers(_py: Python<'_>, obj: &Bound<'_, PyAny>) -> Vec<(String, HandlerKind)> {
    let mut handlers = Vec::new();

    let dir = match obj.dir() {
        Ok(d) => d,
        Err(_) => return handlers,
    };

    for attr_name_obj in dir.iter() {
        let attr_name: String = match attr_name_obj.extract() {
            Ok(s) => s,
            Err(_) => continue,
        };

        if attr_name.starts_with("__") {
            continue;
        }

        let attr = match obj.getattr(attr_name.as_str()) {
            Ok(a) => a,
            Err(_) => continue,
        };

        if attr.hasattr("_is_main").unwrap_or(false) {
            handlers.push((attr_name.clone(), HandlerKind::Main));
        }
        if attr.hasattr("_is_clones").unwrap_or(false) {
            handlers.push((attr_name.clone(), HandlerKind::Clone));
        }
        if let Ok(true) = attr.hasattr("_key_event") {
            if let Ok(kv) = attr.getattr("_key_event") {
                if let Ok((key, mode)) = kv.extract::<(String, String)>() {
                    handlers.push((attr_name.clone(), HandlerKind::Key { key, mode }));
                }
            }
        }
        if let Ok(true) = attr.hasattr("_broadcast_event") {
            if let Ok(ev) = attr.getattr("_broadcast_event") {
                if let Ok(event) = ev.extract::<String>() {
                    handlers.push((attr_name.clone(), HandlerKind::Broadcast { event }));
                }
            }
        }
        if attr.hasattr("_is_sprite_clicked").unwrap_or(false) {
            handlers.push((attr_name.clone(), HandlerKind::SpriteClicked));
        }
        if let Ok(true) = attr.hasattr("_edge_collision") {
            if let Ok(ev) = attr.getattr("_edge_collision") {
                if let Ok(edge) = ev.extract::<String>() {
                    handlers.push((attr_name.clone(), HandlerKind::EdgeCollision { edge }));
                }
            }
        }
        if let Ok(true) = attr.hasattr("_sprite_collision") {
            if let Ok(ev) = attr.getattr("_sprite_collision") {
                // Single string: @on_sprite_collision("Enemy")
                if let Ok(target) = ev.extract::<String>() {
                    handlers.push((attr_name.clone(), HandlerKind::SpriteCollision { target }));
                }
                // List of strings: stacked @on_sprite_collision("A") @on_sprite_collision("B")
                else if let Ok(targets) = ev.extract::<Vec<String>>() {
                    for target in targets {
                        handlers.push((attr_name.clone(), HandlerKind::SpriteCollision { target }));
                    }
                }
            }
        }
        if let Ok(true) = attr.hasattr("_mouse_event") {
            if let Ok(ev) = attr.getattr("_mouse_event") {
                if let Ok((button, mode)) = ev.extract::<(u32, String)>() {
                    handlers.push((attr_name.clone(), HandlerKind::Mouse { button, mode }));
                }
            }
        }
    }

    handlers
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::PyModule;
    use std::ffi::CString;

    fn make_node2d() -> Py<PyAny> {
        Python::with_gil(|py| {
            let code = CString::new(
                r#"
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class TestNode:
    _scrawl_node_kind = "node2d"

    def __init__(self):
        self._scrawl_node_id = 10
        self.name = "dynamic"
        self.position = Vec(12.0, 34.0)
        self.rotation = 0.5
        self.scale = Vec(2.0, 3.0)
        self.z_index = 4
        self.visible = True
        self.dirty = True

    def _scrawl_tree_records(self):
        return [(self._scrawl_node_id, None, self._scrawl_node_kind, self)]

    def _take_node_dirty(self):
        dirty = self.dirty
        self.dirty = False
        return dirty

node = TestNode()
"#,
            )
            .unwrap();
            let file = CString::new("runtime_node_test.py").unwrap();
            let name = CString::new("runtime_node_test").unwrap();
            PyModule::from_code(py, &code, &file, &name)
                .unwrap()
                .getattr("node")
                .unwrap()
                .unbind()
        })
    }

    #[test]
    fn dynamic_node2d_add_sync_reparent_and_remove() {
        let node = make_node2d();
        let mut world = World::new();
        world.insert_resource(PythonRuntime::default());
        let first_parent = world.spawn_empty().id();
        let second_parent = world.spawn_empty().id();
        world
            .resource_mut::<PythonRuntime>()
            .nodes
            .insert(1, first_parent);
        world
            .resource_mut::<PythonRuntime>()
            .nodes
            .insert(2, second_parent);
        let mut sprites = Vec::new();

        spawn_dynamic_subtree(&mut world, &node, &mut sprites, Some(1));

        let entity = world.resource::<PythonRuntime>().nodes[&10];
        assert_eq!(world.get::<Parent>(entity).unwrap().get(), first_parent);
        assert_eq!(
            world.get::<Transform>(entity).unwrap().translation,
            Vec3::new(12.0, 34.0, 4.0)
        );

        Python::with_gil(|py| {
            let bound = node.bind(py);
            bound
                .getattr("position")
                .unwrap()
                .setattr("x", 80.0)
                .unwrap();
            bound.setattr("dirty", true).unwrap();
            sync_python_nodes(&mut world, py);
        });
        assert_eq!(world.get::<Transform>(entity).unwrap().translation.x, 80.0);

        reparent_python_node(&mut world, 10, 2);
        assert_eq!(world.get::<Parent>(entity).unwrap().get(), second_parent);

        despawn_python_subtree(&mut world, 10, &node, &mut sprites);
        assert!(!world.resource::<PythonRuntime>().nodes.contains_key(&10));
        assert!(world.get_entity(entity).is_err());
    }
}
