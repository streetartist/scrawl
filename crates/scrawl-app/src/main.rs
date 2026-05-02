//! Scrawl App - The main binary that assembles all engine plugins.
//!
//! Supports two modes:
//! - Standalone: runs a game directly
//! - Editor: runs as a subprocess controlled by the IDE via IPC

use bevy::prelude::*;
use clap::Parser;

use scrawl_core::prelude::*;
use scrawl_core::resources::ScrawlConfig;
use scrawl_render::ScrawlRenderPlugin;
use scrawl_scripting::ScrawlScriptingPlugin;

/// Scrawl Engine - A simple yet powerful 2D game engine
#[derive(Parser, Debug)]
#[command(name = "scrawl-engine", version, about)]
struct Cli {
    /// Run in editor mode (IPC subprocess)
    #[arg(long)]
    editor: bool,

    /// Named pipe / socket path for editor IPC
    #[arg(long)]
    pipe: Option<String>,

    /// Path to the Python script to run
    #[arg(long)]
    script: Option<String>,

    /// Window width
    #[arg(long, default_value_t = 800)]
    width: u32,

    /// Window height
    #[arg(long, default_value_t = 600)]
    height: u32,

    /// Window title
    #[arg(long, default_value = "Scrawl Game")]
    title: String,

    /// Target FPS
    #[arg(long, default_value_t = 60)]
    fps: u32,

    /// Enable debug mode
    #[arg(long)]
    debug: bool,
}

fn main() {
    env_logger::init();
    let cli = Cli::parse();

    log::info!("Scrawl Engine v2.1.2 starting...");
    log::info!(
        "Mode: {}",
        if cli.editor { "Editor" } else { "Standalone" }
    );

    let config = ScrawlConfig {
        width: cli.width,
        height: cli.height,
        title: cli.title.clone(),
        fps: cli.fps,
        fullscreen: false,
        debug: cli.debug,
    };

    let mut app = App::new();

    // Default Bevy plugins with our window configuration
    app.add_plugins(
        DefaultPlugins.set(WindowPlugin {
            primary_window: Some(Window {
                title: cli.title.clone(),
                resolution: (cli.width as f32, cli.height as f32).into(),
                ..default()
            }),
            ..default()
        }),
    );

    // Scrawl core plugins
    app.insert_resource(config);
    app.add_plugins(ScrawlCorePlugin);
    app.add_plugins(ScrawlRenderPlugin);
    app.add_plugins(ScrawlScriptingPlugin {
        script_path: cli.script,
        hot_reload: !cli.editor, // disable hot-reload in editor mode (IDE controls reloads)
        ..default()
    });

    // Phase 2+ plugins (uncomment as they become available):
    // app.add_plugins(ScrawlPhysicsPlugin);
    // app.add_plugins(ScrawlAudioPlugin);
    // app.add_plugins(ScrawlAnimationPlugin);
    // app.add_plugins(ScrawlTilemapPlugin);
    // app.add_plugins(ScrawlParticlePlugin);
    // app.add_plugins(ScrawlNavigationPlugin);
    // app.add_plugins(ScrawlUIPlugin);

    // Editor mode: add IPC server plugin
    if cli.editor {
        log::info!("Editor IPC pipe: {:?}", cli.pipe);
        // Phase 4: app.add_plugins(ScrawlEditorServerPlugin { pipe: cli.pipe });
    }

    // Add a startup system to display engine info
    app.add_systems(Startup, print_engine_info);

    log::info!("Entering Bevy event loop...");
    app.run();
}

fn print_engine_info(config: Res<ScrawlConfig>) {
    log::info!(
        "Scrawl Engine running: {}x{} @ {}fps, debug={}",
        config.width,
        config.height,
        config.fps,
        config.debug
    );
}
