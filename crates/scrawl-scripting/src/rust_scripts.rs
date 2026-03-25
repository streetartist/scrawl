//! Rust script execution system.
//!
//! Executes on_update for all entities with RustScriptRef components.

use bevy::prelude::*;

use crate::context::ScriptContext;
use crate::traits::ScrawlScript;

/// Component that holds a Rust script instance.
#[derive(Component)]
pub struct RustScriptRef {
    pub script: Box<dyn ScrawlScript>,
    pub started: bool,
}

/// System that executes Rust scripts each frame.
pub fn execute_rust_scripts(world: &mut World) {
    // Collect all entities with RustScriptRef
    let entities: Vec<Entity> = world
        .query_filtered::<Entity, With<RustScriptRef>>()
        .iter(world)
        .collect();

    for entity in entities {
        // Temporarily take the script out of the world to avoid borrow conflicts
        let mut script_ref = match world.get_mut::<RustScriptRef>(entity) {
            Some(mut s) => {
                let script = std::mem::replace(
                    &mut s.script,
                    Box::new(NoopScript),
                );
                let started = s.started;
                s.started = true;
                (script, started)
            }
            None => continue,
        };

        // Run the script
        {
            let mut ctx = ScriptContext::new(entity, world);
            if !script_ref.1 {
                script_ref.0.on_start(&mut ctx);
            }
            script_ref.0.on_update(&mut ctx);
        }

        // Put the script back
        if let Some(mut s) = world.get_mut::<RustScriptRef>(entity) {
            s.script = script_ref.0;
        }
    }
}

/// A no-op script used as a placeholder during temporary extraction.
struct NoopScript;
impl ScrawlScript for NoopScript {}
