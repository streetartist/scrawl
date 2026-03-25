//! Runtime integration - connects Python scripts to the Bevy ECS.
//!
//! All Python interaction happens in a single exclusive system per frame,
//! acquiring the GIL only once to minimize overhead.

use bevy::prelude::*;
use pyo3::prelude::*;
use std::collections::HashMap;
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

            // --- 5. Advance all active coroutines ---
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

            // --- 6. Sync Python state → ECS (Y-up: Python matches Bevy, no flip) ---
            let obj = sprite.py_object.bind(py);
            let entity = sprite.entity;

            if let Some(mut t2d) = world.get_mut::<Transform2D>(entity) {
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

            // Sync current costume
            if let Ok(costume_name) = obj.getattr("_current_costume").and_then(|v| v.extract::<String>()) {
                if let Some(mut costumes) = world.get_mut::<CostumeSet>(entity) {
                    costumes.switch_to(&costume_name);
                }
            }
        }
    });

    // --- Process command queue from Python ---
    let commands = Python::with_gil(|py| {
        process_python_commands(py, &mut sprites)
    });

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
                if let Some(i) = idx_to_remove {
                    sprites.remove(i);
                }
            }
            PythonCommand::Broadcast(event) => {
                world.send_event(BroadcastEvent(event));
            }
            PythonCommand::SetText { ptr_id, text, font_size, color } => {
                // Find existing text entity for this sprite, or spawn new one

                // Get sprite position from the sprites list
                let sprite_pos = sprites.iter().find(|s| {
                    Python::with_gil(|py| s.py_object.bind(py).as_ptr() as usize == ptr_id)
                }).and_then(|s| {
                    Python::with_gil(|py| {
                        let obj = s.py_object.bind(py);
                        let x = obj.getattr("x").and_then(|v| v.extract::<f32>()).unwrap_or(400.0);
                        let y = obj.getattr("y").and_then(|v| v.extract::<f32>()).unwrap_or(300.0);
                        Some(Vec2::new(x, y))
                    })
                }).unwrap_or(Vec2::new(400.0, 300.0));

                // Find existing text entity
                let mut existing = None;
                let mut text_query = world.query::<(Entity, &ScrawlTextDisplay)>();
                for (e, td) in text_query.iter(world) {
                    if td.owner_ptr == ptr_id {
                        existing = Some(e);
                        break;
                    }
                }

                if text.is_empty() {
                    // Clear text
                    if let Some(e) = existing {
                        world.despawn(e);
                    }
                } else if let Some(e) = existing {
                    // Update existing
                    if let Some(mut t) = world.get_mut::<Text2d>(e) {
                        **t = text;
                    }
                    if let Some(mut tr) = world.get_mut::<Transform>(e) {
                        tr.translation.x = sprite_pos.x;
                        tr.translation.y = sprite_pos.y;
                    }
                } else {
                    // Spawn new text entity
                    world.spawn((
                        ScrawlTextDisplay { owner_ptr: ptr_id },
                        Text2d::new(text),
                        TextFont { font_size, ..default() },
                        TextColor(Color::srgb(color[0], color[1], color[2])),
                        Transform::from_xyz(sprite_pos.x, sprite_pos.y, 500.0),
                    ));
                }
            }
        }
    }

    // Put sprites back
    world.resource_mut::<PythonRuntime>().sprites = sprites;
}

enum PythonCommand {
    Clone(Py<PyAny>),
    Delete(usize),
    Broadcast(String),
    SetText { ptr_id: usize, text: String, font_size: f32, color: [f32; 3] },
}

/// Marker for text entities spawned by set_text().
#[derive(Component)]
struct ScrawlTextDisplay {
    owner_ptr: usize,
}

/// Read and drain the Python-side _scrawl_command_queue.
fn process_python_commands(py: Python<'_>, sprites: &mut Vec<PythonSpriteInstance>) -> Vec<PythonCommand> {
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

    let items: Vec<pyo3::Bound<'_, PyAny>> = match queue.iter() {
        Ok(iter) => iter.filter_map(|i| i.ok()).collect(),
        Err(_) => return commands,
    };

    for item in &items {
        if let Ok(tuple) = item.downcast::<pyo3::types::PyTuple>() {
            if tuple.len() < 2 { continue; }
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
