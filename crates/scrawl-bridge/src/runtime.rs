//! Runtime integration - connects Python scripts to the Bevy ECS.
//!
//! All Python interaction happens in a single exclusive system per frame,
//! acquiring the GIL only once to minimize overhead.

use bevy::prelude::*;
use bevy_kira_audio::Audio;
use pyo3::prelude::*;
use scrawl_audio::AudioManager;
use std::collections::{HashMap, HashSet};
use std::time::{Duration, Instant};

use scrawl_core::components::*;
use scrawl_core::events::*;
use scrawl_core::schedule::ScrawlSet;

/// A registered Python sprite instance with its handlers.
#[derive(Debug)]
pub struct PythonSpriteInstance {
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
    pub budget_ms: u64,
}

impl Default for PythonRuntime {
    fn default() -> Self {
        Self {
            sprites: Vec::new(),
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
    }
}

/// Single exclusive system that does ALL Python work in one GIL acquisition.
fn python_frame_system(world: &mut World) {
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
    Python::with_gil(|py| {
        let deadline = Instant::now() + Duration::from_millis(budget_ms);

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
                let other_name = entity_names.get(&other_entity).map(|s| s.as_str()).unwrap_or("");
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
                            let coro_key = format!("mouse_{}_{}_{}", method_name, event_button, event_mode);
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
                                    sprite.py_object.bind(py)
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
            if let Some(mut vis) = world.get_mut::<Visible>(entity) {
                if let Ok(visible) = obj.getattr("visible").and_then(|v| v.extract::<bool>()) {
                    vis.0 = visible;
                }
            }

            if let Some(mut sprite_color) = world.get_mut::<SpriteColor>(entity) {
                if let Ok((r, g, b)) = obj.getattr("color").and_then(|v| v.extract::<(u8, u8, u8)>()) {
                    sprite_color.0 = Color::srgb(
                        r as f32 / 255.0,
                        g as f32 / 255.0,
                        b as f32 / 255.0,
                    );
                }
            }

            sync_pen_state_from_python(world, entity, &obj, previous_position);

            // Sync current costume
            if let Ok(costume_name) = obj.getattr("_current_costume").and_then(|v| v.extract::<String>()) {
                if let Some(mut costumes) = world.get_mut::<CostumeSet>(entity) {
                    costumes.switch_to(&costume_name);
                }
            }
        }
    });

    // --- Process command queue from Python ---
    let commands = Python::with_gil(process_python_commands);

    // Execute commands on the ECS world
    for cmd in commands {
        match cmd {
            PythonCommand::Clone(new_sprite_py) => {
                spawn_clone(world, &new_sprite_py, &mut sprites);
            }
            PythonCommand::Delete(ptr_id) => {
                let mut idx_to_remove = None;
                for (i, s) in sprites.iter().enumerate() {
                    Python::with_gil(|py| {
                        if s.py_object.bind(py).as_ptr() as usize == ptr_id {
                            idx_to_remove = Some(i);
                            world.despawn(s.entity);
                        }
                    });
                    if idx_to_remove.is_some() { break; }
                }
                despawn_text_displays_for_owner(world, ptr_id);
                if let Some(i) = idx_to_remove {
                    sprites.remove(i);
                }
            }
            PythonCommand::Broadcast(event) => {
                world.send_event(BroadcastEvent(event));
            }
            PythonCommand::SetText { ptr_id, text, font_size, color } => {
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
            PythonCommand::Say { ptr_id, text, duration_ms } => {
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
            PythonCommand::PlayMusic { path, loops, volume } => {
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
    Clone(Py<PyAny>),
    Delete(usize),
    Broadcast(String),
    SetText { ptr_id: usize, text: String, font_size: f32, color: [f32; 3] },
    Say { ptr_id: usize, text: String, duration_ms: u64 },
    PlaySound { path: String, volume: Option<f64> },
    PlayMusic { path: String, loops: i32, volume: Option<f64> },
    StopMusic,
    PauseMusic,
    ResumeMusic,
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

    let module = match py.import("scrawl_v2.sprite") {
        Ok(m) => m,
        Err(_) => match py.import("scrawl.sprite") {
            Ok(m) => m,
            Err(_) => return commands,
        },
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
            if tuple.is_empty() { continue; }
            let cmd_type: String = match tuple.get_item(0).and_then(|v| v.extract()) {
                Ok(s) => s,
                Err(_) => continue,
            };
            match cmd_type.as_str() {
                "clone" => {
                    if let Ok(sprite_obj) = tuple.get_item(1) {
                        commands.push(PythonCommand::Clone(sprite_obj.unbind()));
                    }
                }
                "delete" => {
                    if let Ok(sprite_obj) = tuple.get_item(1) {
                        let del_id = sprite_obj.as_ptr() as usize;
                        commands.push(PythonCommand::Delete(del_id));
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
                            let text = tuple.get_item(2).and_then(|v| v.extract::<String>()).unwrap_or_default();
                            let font_size = tuple.get_item(3).and_then(|v| v.extract::<f32>()).unwrap_or(20.0);
                            let color = if let Ok(c) = tuple.get_item(4) {
                                if let Ok((r, g, b)) = c.extract::<(u8, u8, u8)>() {
                                    [r as f32 / 255.0, g as f32 / 255.0, b as f32 / 255.0]
                                } else {
                                    [1.0, 1.0, 1.0]
                                }
                            } else {
                                [1.0, 1.0, 1.0]
                            };
                            commands.push(PythonCommand::SetText { ptr_id, text, font_size, color });
                        }
                    }
                }
                "say" => {
                    // ("say", sprite_obj, text_str, duration_ms)
                    if tuple.len() >= 4 {
                        if let Ok(sprite_obj) = tuple.get_item(1) {
                            let ptr_id = sprite_obj.as_ptr() as usize;
                            let text = tuple.get_item(2).and_then(|v| v.extract::<String>()).unwrap_or_default();
                            let duration_ms = tuple.get_item(3).and_then(|v| v.extract::<u64>()).unwrap_or(2000);
                            commands.push(PythonCommand::Say { ptr_id, text, duration_ms });
                        }
                    }
                }
                "play_sound" => {
                    if tuple.len() >= 2 {
                        let path = tuple.get_item(1).and_then(|v| v.extract::<String>()).unwrap_or_default();
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
                        let path = tuple.get_item(1).and_then(|v| v.extract::<String>()).unwrap_or_default();
                        let loops = tuple.get_item(2).and_then(|v| v.extract::<i32>()).unwrap_or(-1);
                        let volume = if tuple.len() >= 4 {
                            tuple.get_item(3).and_then(|v| v.extract::<f64>()).ok()
                        } else {
                            None
                        };
                        if !path.is_empty() {
                            commands.push(PythonCommand::PlayMusic { path, loops, volume });
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
fn start_handler(py: Python<'_>, sprite: &mut PythonSpriteInstance, method_name: &str, coro_key: String) {
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
    camera.viewport_to_world_2d(camera_transform, screen_pos).ok()
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

    Vec2::new(
        delta.x * cos - delta.y * sin,
        delta.x * sin + delta.y * cos,
    )
}

fn click_half_size(
    t2d: &Transform2D,
    sprite: Option<&bevy::sprite::Sprite>,
    mask: Option<&CollisionMask>,
) -> Vec2 {
    let base = click_base_size(sprite, mask);

    Vec2::new(base.x * t2d.scale.x.abs(), base.y * t2d.scale.y.abs()) / 2.0
}

fn click_base_size(
    sprite: Option<&bevy::sprite::Sprite>,
    mask: Option<&CollisionMask>,
) -> Vec2 {
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

fn sprite_position_for_ptr(sprites: &[PythonSpriteInstance], ptr_id: usize) -> Vec2 {
    sprites
        .iter()
        .find(|sprite| Python::with_gil(|py| sprite.py_object.bind(py).as_ptr() as usize == ptr_id))
        .map(|sprite| {
            Python::with_gil(|py| {
                let obj = sprite.py_object.bind(py);
                let x = obj.getattr("x").and_then(|v| v.extract::<f32>()).unwrap_or(400.0);
                let y = obj.getattr("y").and_then(|v| v.extract::<f32>()).unwrap_or(300.0);
                Vec2::new(x, y)
            })
        })
        .unwrap_or(Vec2::new(400.0, 300.0))
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

fn find_text_display_entity(world: &mut World, ptr_id: usize, kind: TextDisplayKind) -> Option<Entity> {
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

    let sprite_pos = sprite_position_for_ptr(sprites, ptr_id);

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
        TextFont { font_size, ..default() },
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

            let sprite_pos = sprite_position_for_ptr(sprites, display.owner_ptr);
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

/// Spawn a cloned sprite entity at runtime.
fn spawn_clone(
    world: &mut World,
    py_sprite: &Py<PyAny>,
    sprites: &mut Vec<PythonSpriteInstance>,
) {
    Python::with_gil(|py| {
        let obj = py_sprite.bind(py);

        let name = obj.getattr("name").and_then(|v| v.extract::<String>()).unwrap_or_else(|_| "Clone".into());
        let x = obj.getattr("x").and_then(|v| v.extract::<f32>()).unwrap_or(400.0);
        let y = obj.getattr("y").and_then(|v| v.extract::<f32>()).unwrap_or(300.0);
        let dir = obj.getattr("direction").and_then(|v| v.extract::<f32>()).unwrap_or(90.0);
        let size = obj.getattr("size").and_then(|v| v.extract::<f32>()).unwrap_or(1.0);
        let visible = obj.getattr("visible").and_then(|v| v.extract::<bool>()).unwrap_or(true);
        let collision_type = obj.getattr("collision_type").and_then(|v| v.extract::<String>()).unwrap_or_else(|_| "rect".into());

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

        let bevy_sprite = if let Some(ref img) = first_image {
            Sprite { image: img.clone(), color: Color::WHITE, ..default() }
        } else {
            Sprite { color, custom_size: Some(Vec2::new(40.0, 40.0)), ..default() }
        };

        let entity = world.spawn((
            bevy_sprite,
            Transform::from_xyz(x, y, 0.0).with_scale(Vec3::splat(size)),
            ScrawlName(name.clone()),
            ScrawlId::default(),
            Transform2D {
                position: Vec2::new(x, y),
                rotation_degrees: dir,
                scale: Vec2::splat(size),
            },
            Visible(visible),
            SpriteColor(if first_image.is_some() { Color::WHITE } else { color }),
            CollisionShape { kind: collision_kind, radius: None },
            PenState::default(),
            NodeType(NodeKind::Sprite),
            IsClone,
            costume_set,
        )).id();

        // Scan for @as_clones handlers and start them
        let handlers = scan_python_handlers(py, &obj);
        let mut coroutines = HashMap::new();
        let wake_times = HashMap::new();

        for (method_name, kind) in &handlers {
            if matches!(kind, HandlerKind::Clone) {
                if let Ok(gen) = obj.call_method0(method_name.as_str()) {
                    if gen.hasattr("__next__").unwrap_or(false) {
                        coroutines.insert(format!("clone_{}", method_name), gen.unbind());
                    }
                }
            }
        }

        // Set scene reference on the Python sprite
        // (so face_towards etc. can find other sprites)
        // obj is the new clone's Python object

        sprites.push(PythonSpriteInstance {
            py_object: py_sprite.clone_ref(py),
            entity,
            coroutines,
            wake_times,
            handlers,
        });
    });
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
