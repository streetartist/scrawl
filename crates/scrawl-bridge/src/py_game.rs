//! PyGame - Python wrapper for the Game/Engine lifecycle.

use bevy::prelude::*;
use pyo3::prelude::*;
use std::collections::HashMap;

use scrawl_audio::ScrawlAudioPlugin;
use scrawl_core::components::*;
use scrawl_core::resources::ScrawlConfig;
use scrawl_core::ScrawlCorePlugin;
use scrawl_render::ScrawlRenderPlugin;
use scrawl_scripting::ScrawlScriptingPlugin;

use crate::runtime::{
    scan_python_handlers, HandlerKind, PythonNodeId, PythonRuntime, PythonRuntimePlugin,
    PythonSpriteInstance,
};

/// The main Game class exposed to Python.
///
/// Usage from Python:
/// ```python
/// from scrawl import Game
/// game = Game(width=800, height=600, title="My Game")
/// game.set_scene(my_scene)
/// game.run()
/// ```
#[pyclass(name = "NativeGame")]
#[derive(Debug)]
pub struct PyGame {
    width: u32,
    height: u32,
    title: String,
    fps: u32,
    fullscreen: bool,
    debug: bool,
    vsync: bool,
    /// Stored scenes: list of (scene_py_obj, background_color, background_image, sprite_py_objs)
    scenes: Vec<SceneInfo>,
    active_scene_index: Option<usize>,
}

#[derive(Debug)]
struct SceneInfo {
    _name: String,
    background_color: [f32; 4],
    _background_image: Option<String>,
    nodes: Vec<PythonNodeRecord>,
}

#[derive(Debug)]
struct PythonNodeRecord {
    node_id: u64,
    parent_id: Option<u64>,
    kind: String,
    py_object: Py<PyAny>,
}

#[pymethods]
impl PyGame {
    #[new]
    #[pyo3(signature = (width=800, height=600, title="Scrawl Game", fps=60, fullscreen=false, debug=false, vsync=true))]
    fn new(
        width: u32,
        height: u32,
        title: &str,
        fps: u32,
        fullscreen: bool,
        debug: bool,
        vsync: bool,
    ) -> Self {
        Self {
            width,
            height,
            title: title.to_string(),
            fps,
            fullscreen,
            debug,
            vsync,
            scenes: Vec::new(),
            active_scene_index: None,
        }
    }

    /// Set the active scene. Accepts any Python Scene object.
    fn set_scene(&mut self, py: Python<'_>, scene: &Bound<'_, PyAny>) -> PyResult<()> {
        let info = extract_scene_info(py, scene)?;
        self.scenes.push(info);
        self.active_scene_index = Some(self.scenes.len() - 1);
        Ok(())
    }

    /// Run the game. This blocks until the window is closed.
    fn run(&mut self, py: Python<'_>) -> PyResult<()> {
        // Collect all sprite data before entering Bevy (we can't hold PyO3 refs across the GIL boundary)
        let active_idx = self.active_scene_index.unwrap_or(0);
        if active_idx >= self.scenes.len() {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "No scene set. Call game.set_scene() first.",
            ));
        }

        // Build startup data
        let scene = &self.scenes[active_idx];
        let bg_color = scene.background_color;
        let bg_image = scene._background_image.clone();

        // Collect the complete scene tree. Sprite payloads keep their existing
        // rendering/event path; other nodes receive structural ECS entities.
        let generic_nodes = scene
            .nodes
            .iter()
            .filter(|record| record.kind != "sprite")
            .map(|record| extract_generic_node_spawn_data(py, record))
            .collect::<PyResult<Vec<_>>>()?;
        let parent_links = scene
            .nodes
            .iter()
            .map(|record| (record.node_id, record.parent_id))
            .collect::<Vec<_>>();

        let mut sprite_data: Vec<SpriteSpawnData> = Vec::new();
        for node_record in scene.nodes.iter().filter(|record| record.kind == "sprite") {
            let sprite_py = &node_record.py_object;
            let obj = sprite_py.bind(py);

            // Extract costumes: dict {name: path} → Vec<(name, path)>
            let costumes = if let Ok(c) = obj.getattr("_costumes") {
                if let Ok(dict) = c.downcast::<pyo3::types::PyDict>() {
                    dict.iter()
                        .filter_map(|(k, v)| {
                            Some((k.extract::<String>().ok()?, v.extract::<String>().ok()?))
                        })
                        .collect()
                } else {
                    Vec::new()
                }
            } else {
                Vec::new()
            };

            // Extract the Python Sprite's (r, g, b) color property.
            let color = if let Ok(c) = obj.getattr("color") {
                if let Ok((r, g, b)) = c.extract::<(u8, u8, u8)>() {
                    [r as f32 / 255.0, g as f32 / 255.0, b as f32 / 255.0]
                } else {
                    [1.0, 0.4, 0.4]
                }
            } else {
                [1.0, 0.4, 0.4]
            };

            let data = SpriteSpawnData {
                node_id: node_record.node_id,
                name: obj.getattr("name")?.extract::<String>()?,
                x: obj.getattr("x")?.extract::<f32>()?,
                y: obj.getattr("y")?.extract::<f32>()?,
                direction: obj.getattr("direction")?.extract::<f32>()?,
                size: obj.getattr("size")?.extract::<f32>()?,
                width: obj
                    .getattr("width")
                    .ok()
                    .and_then(|v| v.extract::<Option<f32>>().ok())
                    .flatten(),
                height: obj
                    .getattr("height")
                    .ok()
                    .and_then(|v| v.extract::<Option<f32>>().ok())
                    .flatten(),
                z_index: obj
                    .getattr("z_index")
                    .and_then(|v| v.extract::<i32>())
                    .unwrap_or(0),
                visible: obj.getattr("visible")?.extract::<bool>()?,
                collision_type: obj
                    .getattr("collision_type")
                    .and_then(|v| v.extract::<String>())
                    .unwrap_or_else(|_| "rect".to_string()),
                color,
                costumes,
                py_object: sprite_py.clone_ref(py),
                handlers: scan_python_handlers(py, &obj),
            };
            sprite_data.push(data);
        }

        let width = self.width;
        let height = self.height;
        let title = self.title.clone();
        let fps = self.fps;
        let debug = self.debug;
        let vsync = self.vsync;
        let fullscreen = self.fullscreen;

        // Release the GIL and run Bevy
        // NOTE: We need to allow other threads during Bevy's run loop
        py.allow_threads(move || {
            let mut app = App::new();

            // Default Bevy plugins
            let present_mode = if vsync {
                bevy::window::PresentMode::AutoVsync
            } else {
                bevy::window::PresentMode::AutoNoVsync
            };

            app.add_plugins(DefaultPlugins.set(WindowPlugin {
                primary_window: Some(Window {
                    title: title.clone(),
                    resolution: (width as f32, height as f32).into(),
                    present_mode,
                    mode: if fullscreen {
                        bevy::window::WindowMode::BorderlessFullscreen(MonitorSelection::Current)
                    } else {
                        bevy::window::WindowMode::Windowed
                    },
                    // Disable system maximize button to avoid Windows modal loop freeze.
                    // Use F11 for fullscreen toggle instead.
                    enabled_buttons: bevy::window::EnabledButtons {
                        maximize: false,
                        ..default()
                    },
                    resizable: true,
                    ..default()
                }),
                ..default()
            }));

            // Scrawl plugins
            app.insert_resource(ScrawlConfig {
                width,
                height,
                title,
                fps,
                fullscreen,
                debug,
            });
            app.add_plugins(ScrawlCorePlugin);
            app.add_plugins(ScrawlRenderPlugin);
            app.add_plugins(ScrawlAudioPlugin);
            app.add_plugins(ScrawlScriptingPlugin::default());
            app.add_plugins(PythonRuntimePlugin);

            // F11 fullscreen toggle (uses BorderlessFullscreen, avoids Windows modal loop)
            app.add_systems(Update, toggle_fullscreen_on_f11);

            // ClearColor = black (for letterbox bars outside viewport)
            // Scene background color is set on the camera (clears within viewport)
            app.insert_resource(ClearColor(Color::BLACK));
            app.insert_resource(scrawl_render::camera::SceneBackgroundColor(Color::srgba(
                bg_color[0],
                bg_color[1],
                bg_color[2],
                bg_color[3],
            )));

            app.insert_resource(PendingNodes {
                generic_nodes,
                sprites: sprite_data,
                parent_links,
            });
            app.insert_resource(PendingBackground {
                image_path: bg_image,
                width: width as f32,
                height: height as f32,
            });

            app.add_systems(Startup, (spawn_scene_background, spawn_nodes_from_python));

            app.run();
        });

        Ok(())
    }

    #[getter]
    fn width(&self) -> u32 {
        self.width
    }

    #[getter]
    fn height(&self) -> u32 {
        self.height
    }

    #[getter]
    fn title(&self) -> &str {
        &self.title
    }

    #[getter]
    fn debug(&self) -> bool {
        self.debug
    }
}

/// Temporary data for spawning sprites.
struct SpriteSpawnData {
    node_id: u64,
    name: String,
    x: f32,
    y: f32,
    direction: f32,
    size: f32,
    width: Option<f32>,
    height: Option<f32>,
    z_index: i32,
    visible: bool,
    collision_type: String,
    color: [f32; 3],
    costumes: Vec<(String, String)>, // (name, path)
    py_object: Py<PyAny>,
    handlers: Vec<(String, HandlerKind)>,
}

#[derive(Resource)]
struct PendingNodes {
    generic_nodes: Vec<GenericNodeSpawnData>,
    sprites: Vec<SpriteSpawnData>,
    parent_links: Vec<(u64, Option<u64>)>,
}

struct GenericNodeSpawnData {
    node_id: u64,
    name: String,
    kind: GenericNodeKind,
    py_object: Py<PyAny>,
}

enum GenericNodeKind {
    Scene,
    Empty,
    Node2D {
        position: Vec2,
        rotation: f32,
        scale: Vec2,
        z_index: i32,
        visible: bool,
    },
}

#[derive(Resource)]
struct PendingBackground {
    image_path: Option<String>,
    width: f32,
    height: f32,
}

fn spawn_scene_background(
    mut commands: Commands,
    pending: Res<PendingBackground>,
    asset_server: Res<AssetServer>,
) {
    let Some(path) = pending.image_path.as_ref() else {
        return;
    };

    let image: Handle<Image> = asset_server.load(path.clone());
    commands.spawn((
        Sprite {
            image,
            custom_size: Some(Vec2::new(pending.width, pending.height)),
            color: Color::WHITE,
            ..default()
        },
        Transform::from_xyz(pending.width / 2.0, pending.height / 2.0, -100.0),
        Name::new("SceneBackground"),
    ));
}

/// Startup system: spawn the Python scene tree as Bevy entities.
fn spawn_nodes_from_python(
    mut commands: Commands,
    pending: Res<PendingNodes>,
    mut runtime: ResMut<PythonRuntime>,
    asset_server: Res<AssetServer>,
    _config: Res<ScrawlConfig>,
) {
    let mut entity_by_node_id = HashMap::new();

    for data in &pending.generic_nodes {
        let entity = match &data.kind {
            GenericNodeKind::Scene => commands
                .spawn((
                    Transform::default(),
                    ScrawlName(data.name.clone()),
                    ScrawlId::default(),
                    NodeType(NodeKind::Empty),
                    PythonNodeId(data.node_id),
                    SceneRoot,
                ))
                .id(),
            GenericNodeKind::Empty => commands
                .spawn((
                    Transform::default(),
                    ScrawlName(data.name.clone()),
                    ScrawlId::default(),
                    NodeType(NodeKind::Empty),
                    PythonNodeId(data.node_id),
                ))
                .id(),
            GenericNodeKind::Node2D {
                position,
                rotation,
                scale,
                z_index,
                visible,
            } => commands
                .spawn((
                    Transform::from_xyz(position.x, position.y, *z_index as f32)
                        .with_rotation(Quat::from_rotation_z(*rotation))
                        .with_scale(Vec3::new(scale.x, scale.y, 1.0)),
                    if *visible {
                        Visibility::Inherited
                    } else {
                        Visibility::Hidden
                    },
                    ScrawlName(data.name.clone()),
                    ScrawlId::default(),
                    NodeType(NodeKind::Empty),
                    PythonNodeId(data.node_id),
                    Visible(*visible),
                ))
                .id(),
        };
        entity_by_node_id.insert(data.node_id, entity);
        runtime.nodes.insert(data.node_id, entity);
    }

    Python::with_gil(|py| {
        for data in &pending.generic_nodes {
            runtime
                .node_objects
                .insert(data.node_id, data.py_object.clone_ref(py));
            let _ = data.py_object.bind(py).call_method0("_take_node_dirty");
        }
        for data in &pending.sprites {
            let collision_kind = match data.collision_type.as_str() {
                "circle" => CollisionKind::Circle,
                "mask" => CollisionKind::Mask,
                _ => CollisionKind::Rect,
            };

            let sprite_color = Color::srgb(data.color[0], data.color[1], data.color[2]);

            // Build CostumeSet and load first image
            let mut costume_set = CostumeSet::default();
            let mut first_image: Option<Handle<Image>> = None;

            for (cname, cpath) in &data.costumes {
                let handle: Handle<Image> = asset_server.load(cpath.clone());
                if first_image.is_none() {
                    first_image = Some(handle.clone());
                }
                costume_set.costumes.push(CostumeEntry {
                    name: cname.clone(),
                    path: cpath.clone(),
                    handle: Some(handle),
                });
            }

            // Build the Bevy Sprite
            let custom_size = custom_sprite_size(data.width, data.height, first_image.is_some());
            let bevy_sprite = if let Some(ref img) = first_image {
                // Has costume image: use WHITE (no tint), color is only for default shapes
                Sprite {
                    image: img.clone(),
                    color: Color::WHITE,
                    custom_size,
                    ..default()
                }
            } else {
                // No costume — render as colored shape
                Sprite {
                    color: sprite_color,
                    custom_size,
                    ..default()
                }
            };

            let entity = commands
                .spawn((
                    bevy_sprite,
                    Transform::from_xyz(data.x, data.y, data.z_index as f32)
                        .with_scale(Vec3::splat(data.size)),
                    ScrawlName(data.name.clone()),
                    ScrawlId::default(),
                    Transform2D {
                        position: Vec2::new(data.x, data.y),
                        rotation_degrees: data.direction,
                        scale: Vec2::splat(data.size),
                    },
                    Visible(data.visible),
                    SpriteColor(if first_image.is_some() {
                        Color::WHITE
                    } else {
                        sprite_color
                    }),
                    CollisionShape {
                        kind: collision_kind,
                        radius: None,
                    },
                    PenState::default(),
                    NodeType(NodeKind::Sprite),
                    PythonNodeId(data.node_id),
                    costume_set,
                ))
                .id();

            // Start @as_main coroutines
            let mut coroutines = HashMap::new();
            let wake_times = HashMap::new();

            for (method_name, kind) in &data.handlers {
                if matches!(kind, HandlerKind::Main) {
                    // Call the method to get a generator
                    let obj = data.py_object.bind(py);
                    match obj.call_method0(method_name.as_str()) {
                        Ok(gen) => {
                            if gen.hasattr("__next__").unwrap_or(false) {
                                coroutines.insert(format!("main_{}", method_name), gen.unbind());
                            }
                        }
                        Err(e) => {
                            eprintln!(
                                "[Scrawl] Error starting {}.{}: {}",
                                data.name, method_name, e
                            );
                        }
                    }
                }
            }

            // Register in the Python runtime
            let _ = data.py_object.bind(py).call_method0("_take_dirty");
            runtime.sprites.push(PythonSpriteInstance {
                node_id: data.node_id,
                py_object: data.py_object.clone_ref(py),
                entity,
                coroutines,
                wake_times,
                handlers: data.handlers.clone(),
            });

            entity_by_node_id.insert(data.node_id, entity);
            runtime.nodes.insert(data.node_id, entity);
            runtime
                .node_objects
                .insert(data.node_id, data.py_object.clone_ref(py));

            log::info!("Spawned sprite: {} (entity {:?})", data.name, entity);
        }
    });

    for (node_id, parent_id) in &pending.parent_links {
        let Some(parent_id) = parent_id else {
            continue;
        };
        let Some(entity) = entity_by_node_id.get(node_id).copied() else {
            continue;
        };
        let Some(parent_entity) = entity_by_node_id.get(parent_id).copied() else {
            continue;
        };
        commands.entity(entity).set_parent(parent_entity);
    }
}

fn custom_sprite_size(width: Option<f32>, height: Option<f32>, has_image: bool) -> Option<Vec2> {
    match (width, height, has_image) {
        (None, None, true) => None,
        (width, height, _) => Some(Vec2::new(width.unwrap_or(40.0), height.unwrap_or(40.0))),
    }
}

fn extract_generic_node_spawn_data(
    py: Python<'_>,
    record: &PythonNodeRecord,
) -> PyResult<GenericNodeSpawnData> {
    let obj = record.py_object.bind(py);
    let name = obj
        .getattr("name")
        .and_then(|value| value.extract::<String>())
        .unwrap_or_else(|_| "Node".to_string());

    let kind = match record.kind.as_str() {
        "scene" => GenericNodeKind::Scene,
        "node2d" => {
            let position = extract_vector2(&obj, "position", Vec2::ZERO);
            let scale = extract_vector2(&obj, "scale", Vec2::ONE);
            let rotation = obj
                .getattr("rotation")
                .and_then(|value| value.extract::<f32>())
                .unwrap_or(0.0);
            let z_index = obj
                .getattr("z_index")
                .and_then(|value| value.extract::<i32>())
                .unwrap_or(0);
            let visible = obj
                .getattr("visible")
                .and_then(|value| value.extract::<bool>())
                .unwrap_or(true);
            GenericNodeKind::Node2D {
                position,
                rotation,
                scale,
                z_index,
                visible,
            }
        }
        _ => GenericNodeKind::Empty,
    };

    Ok(GenericNodeSpawnData {
        node_id: record.node_id,
        name,
        kind,
        py_object: record.py_object.clone_ref(py),
    })
}

fn extract_vector2(obj: &Bound<'_, PyAny>, attr: &str, fallback: Vec2) -> Vec2 {
    let Ok(value) = obj.getattr(attr) else {
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

/// Extract scene info from a Python Scene object.
fn extract_scene_info(_py: Python<'_>, scene: &Bound<'_, PyAny>) -> PyResult<SceneInfo> {
    let name = scene
        .getattr("name")
        .and_then(|v| v.extract::<String>())
        .unwrap_or_else(|_| "Scene".to_string());

    let bg_color = if let Ok(bc) = scene.getattr("_background_color") {
        if let Ok((r, g, b)) = bc.extract::<(u8, u8, u8)>() {
            [r as f32 / 255.0, g as f32 / 255.0, b as f32 / 255.0, 1.0]
        } else {
            [1.0, 1.0, 1.0, 1.0]
        }
    } else {
        [1.0, 1.0, 1.0, 1.0]
    };

    let bg_image = scene
        .getattr("_background_image")
        .ok()
        .and_then(|v| v.extract::<Option<String>>().ok())
        .flatten();

    let records = scene.call_method0("_scrawl_tree_records")?;
    let mut nodes = Vec::new();
    for item in records.try_iter()? {
        let item = item?;
        let (node_id, parent_id, kind, py_object) =
            item.extract::<(u64, Option<u64>, String, Py<PyAny>)>()?;
        nodes.push(PythonNodeRecord {
            node_id,
            parent_id,
            kind,
            py_object,
        });
    }

    Ok(SceneInfo {
        _name: name,
        background_color: bg_color,
        _background_image: bg_image,
        nodes,
    })
}

/// F11 toggles borderless fullscreen (avoids the Windows modal loop freeze).
fn toggle_fullscreen_on_f11(keyboard: Res<ButtonInput<KeyCode>>, mut windows: Query<&mut Window>) {
    if keyboard.just_pressed(KeyCode::F11) {
        if let Ok(mut window) = windows.get_single_mut() {
            window.mode = match window.mode {
                bevy::window::WindowMode::Windowed => {
                    bevy::window::WindowMode::BorderlessFullscreen(MonitorSelection::Current)
                }
                _ => bevy::window::WindowMode::Windowed,
            };
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generic_nodes_create_a_registered_ecs_hierarchy() {
        let (scene_object, node_object) = Python::with_gil(|py| (py.None(), py.None()));
        let mut app = App::new();
        app.add_plugins((MinimalPlugins, AssetPlugin::default()));
        app.init_resource::<PythonRuntime>();
        app.insert_resource(ScrawlConfig::default());
        app.insert_resource(PendingNodes {
            generic_nodes: vec![
                GenericNodeSpawnData {
                    node_id: 1,
                    name: "scene".to_string(),
                    kind: GenericNodeKind::Scene,
                    py_object: scene_object,
                },
                GenericNodeSpawnData {
                    node_id: 2,
                    name: "group".to_string(),
                    kind: GenericNodeKind::Node2D {
                        position: Vec2::new(12.0, 34.0),
                        rotation: 0.5,
                        scale: Vec2::new(2.0, 3.0),
                        z_index: 4,
                        visible: true,
                    },
                    py_object: node_object,
                },
            ],
            sprites: Vec::new(),
            parent_links: vec![(1, None), (2, Some(1))],
        });
        app.add_systems(Startup, spawn_nodes_from_python);

        app.update();

        let runtime = app.world().resource::<PythonRuntime>();
        let root = runtime.nodes[&1];
        let child = runtime.nodes[&2];
        assert_eq!(
            app.world().get::<PythonNodeId>(root),
            Some(&PythonNodeId(1))
        );
        assert!(app.world().get::<SceneRoot>(root).is_some());
        assert!(app
            .world()
            .get::<Children>(root)
            .is_some_and(|children| children.contains(&child)));

        let transform = app.world().get::<Transform>(child).unwrap();
        assert_eq!(transform.translation, Vec3::new(12.0, 34.0, 4.0));
        assert_eq!(transform.scale, Vec3::new(2.0, 3.0, 1.0));
    }
}
