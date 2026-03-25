//! PyGame - Python wrapper for the Game/Engine lifecycle.

use bevy::prelude::*;
use pyo3::prelude::*;
use std::collections::HashMap;

use scrawl_core::components::*;
use scrawl_core::resources::ScrawlConfig;
use scrawl_core::ScrawlCorePlugin;
use scrawl_render::ScrawlRenderPlugin;
use scrawl_scripting::ScrawlScriptingPlugin;

use crate::runtime::{
    scan_python_handlers, HandlerKind, PythonRuntime, PythonRuntimePlugin, PythonSpriteInstance,
};

/// The main Game class exposed to Python.
///
/// Usage from Python:
/// ```python
/// from scrawl_v2 import *
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
    name: String,
    background_color: [f32; 4],
    background_image: Option<String>,
    sprites: Vec<Py<PyAny>>,
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

        // Collect sprite initial states and Python objects
        let mut sprite_data: Vec<SpriteSpawnData> = Vec::new();
        for sprite_py in &scene.sprites {
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

            // Extract color (v1 uses self.color = (r, g, b) as plain attribute)
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
                name: obj.getattr("name")?.extract::<String>()?,
                x: obj.getattr("x")?.extract::<f32>()?,
                y: obj.getattr("y")?.extract::<f32>()?,
                direction: obj.getattr("direction")?.extract::<f32>()?,
                size: obj.getattr("size")?.extract::<f32>()?,
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

            app.add_plugins(
                DefaultPlugins.set(WindowPlugin {
                    primary_window: Some(Window {
                        title: title.clone(),                        resolution: (width as f32, height as f32).into(),
                        present_mode,
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
                }),
            );

            // Scrawl plugins
            app.insert_resource(ScrawlConfig {
                width,
                height,
                title,
                fps,
                fullscreen: false,
                debug,
            });
            app.add_plugins(ScrawlCorePlugin);
            app.add_plugins(ScrawlRenderPlugin);
            app.add_plugins(ScrawlScriptingPlugin::default());
            app.add_plugins(PythonRuntimePlugin);

            // F11 fullscreen toggle (uses BorderlessFullscreen, avoids Windows modal loop)
            app.add_systems(Update, toggle_fullscreen_on_f11);

            // ClearColor = black (for letterbox bars outside viewport)
            // Scene background color is set on the camera (clears within viewport)
            app.insert_resource(ClearColor(Color::BLACK));
            app.insert_resource(scrawl_render::camera::SceneBackgroundColor(
                Color::srgba(bg_color[0], bg_color[1], bg_color[2], bg_color[3]),
            ));

            // Store sprite data for the startup system
            app.insert_resource(PendingSprites(sprite_data));

            // Startup system to spawn entities
            app.add_systems(Startup, spawn_sprites_from_python);

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
    name: String,
    x: f32,
    y: f32,
    direction: f32,
    size: f32,
    visible: bool,
    collision_type: String,
    color: [f32; 3],
    costumes: Vec<(String, String)>, // (name, path)
    py_object: Py<PyAny>,
    handlers: Vec<(String, HandlerKind)>,
}

#[derive(Resource)]
struct PendingSprites(Vec<SpriteSpawnData>);

/// Startup system: spawn ECS entities from Python sprite data.
fn spawn_sprites_from_python(
    mut commands: Commands,
    pending: Res<PendingSprites>,
    mut runtime: ResMut<PythonRuntime>,
    asset_server: Res<AssetServer>,
    _config: Res<ScrawlConfig>,
) {
    Python::with_gil(|py| {
        for data in &pending.0 {
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
            let bevy_sprite = if let Some(ref img) = first_image {
                // Has costume image: use WHITE (no tint), color is only for default shapes
                Sprite {
                    image: img.clone(),
                    color: Color::WHITE,
                    ..default()
                }
            } else {
                // No costume — render as colored shape
                Sprite {
                    color: sprite_color,
                    custom_size: Some(Vec2::new(40.0, 40.0)),
                    ..default()
                }
            };

            let entity = commands
                .spawn((
                    bevy_sprite,
                    Transform::from_xyz(data.x, data.y, 0.0)
                        .with_scale(Vec3::splat(data.size)),
                    ScrawlName(data.name.clone()),
                    ScrawlId::default(),
                    Transform2D {
                        position: Vec2::new(data.x, data.y),
                        rotation_degrees: data.direction,
                        scale: Vec2::splat(data.size),
                    },
                    Visible(data.visible),
                    SpriteColor(if first_image.is_some() { Color::WHITE } else { sprite_color }),
                    CollisionShape {
                        kind: collision_kind,
                        radius: None,
                    },
                    PenState::default(),
                    NodeType(NodeKind::Sprite),
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
                                coroutines
                                    .insert(format!("main_{}", method_name), gen.unbind());
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
            runtime.sprites.push(PythonSpriteInstance {
                py_object: data.py_object.clone_ref(py),
                entity,
                coroutines,
                wake_times,
                handlers: data.handlers.clone(),
            });

            log::info!("Spawned sprite: {} (entity {:?})", data.name, entity);
        }
    });
}

/// Extract scene info from a Python Scene object.
fn extract_scene_info(py: Python<'_>, scene: &Bound<'_, PyAny>) -> PyResult<SceneInfo> {
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

    let sprites_list = scene.getattr("_sprites")?;
    let mut sprites = Vec::new();
    for item in sprites_list.iter()? {
        sprites.push(item?.unbind());
    }

    Ok(SceneInfo {
        name,
        background_color: bg_color,
        background_image: bg_image,
        sprites,
    })
}

/// F11 toggles borderless fullscreen (avoids the Windows modal loop freeze).
fn toggle_fullscreen_on_f11(
    keyboard: Res<ButtonInput<KeyCode>>,
    mut windows: Query<&mut Window>,
) {
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
