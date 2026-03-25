//! Scrawl Scripting - Script hosting for Python and Rust game scripts
//!
//! This crate provides:
//! - The `ScrawlScript` trait for Rust game scripts
//! - `ScriptContext` for interacting with the ECS from scripts
//! - Python runtime hosting via PyO3
//! - Coroutine/generator scheduler (matching scrawl v1's yield-based pattern)
//! - Hot-reload watching for Python scripts

pub mod context;
pub mod coroutine;
pub mod python_host;
pub mod rust_scripts;
pub mod traits;

use bevy::prelude::*;
use scrawl_core::prelude::ScrawlSet;

/// The scripting plugin that manages Python and Rust script execution.
pub struct ScrawlScriptingPlugin {
    /// Path to the Python script file(s) to load.
    pub script_path: Option<String>,
    /// Whether to enable hot-reload watching.
    pub hot_reload: bool,
    /// Time budget per frame for Python script execution (ms).
    pub python_budget_ms: u64,
}

impl Default for ScrawlScriptingPlugin {
    fn default() -> Self {
        Self {
            script_path: None,
            hot_reload: true,
            python_budget_ms: 8,
        }
    }
}

impl Plugin for ScrawlScriptingPlugin {
    fn build(&self, app: &mut App) {
        app.insert_resource(ScriptingConfig {
            script_path: self.script_path.clone(),
            hot_reload: self.hot_reload,
            python_budget_ms: self.python_budget_ms,
        });

        app.init_resource::<coroutine::CoroutineScheduler>();

        app.add_systems(
            FixedUpdate,
            (
                rust_scripts::execute_rust_scripts,
                coroutine::advance_coroutines,
            )
                .in_set(ScrawlSet::ScriptExec),
        );
    }
}

/// Configuration resource for the scripting system.
#[derive(Resource, Debug, Clone)]
pub struct ScriptingConfig {
    pub script_path: Option<String>,
    pub hot_reload: bool,
    pub python_budget_ms: u64,
}

impl Default for ScriptingConfig {
    fn default() -> Self {
        Self {
            script_path: None,
            hot_reload: true,
            python_budget_ms: 8,
        }
    }
}

/// Prelude for convenient imports.
pub mod prelude {
    pub use crate::context::ScriptContext;
    pub use crate::traits::{InputMode, ScrawlScript};
    pub use crate::ScrawlScriptingPlugin;
}
