//! Scrawl Editor Server - Named pipe IPC server for IDE communication.
//!
//! Runs as a Bevy plugin when the engine is launched in editor mode.
//! Receives commands from the IDE and sends back state updates.

use bevy::prelude::*;
use scrawl_editor_protocol::{EngineToIde, IdeToEngine};
use std::collections::VecDeque;
use std::io::{Read, Write};
use std::sync::{Arc, Mutex};

/// Editor server plugin. Only active when `--editor` flag is passed.
pub struct ScrawlEditorServerPlugin {
    pub pipe_name: Option<String>,
}

impl Plugin for ScrawlEditorServerPlugin {
    fn build(&self, app: &mut App) {
        let pipe_name = self.pipe_name.clone().unwrap_or_else(|| {
            format!("\\\\.\\pipe\\scrawl_editor_{}", std::process::id())
        });

        app.insert_resource(EditorConnection {
            pipe_name,
            incoming: Arc::new(Mutex::new(VecDeque::new())),
            outgoing: Arc::new(Mutex::new(VecDeque::new())),
            connected: false,
        });

        app.add_systems(Update, process_editor_messages);

        log::info!("Editor server plugin initialized");
    }
}

/// Resource holding the editor connection state.
#[derive(Resource)]
pub struct EditorConnection {
    pub pipe_name: String,
    pub incoming: Arc<Mutex<VecDeque<IdeToEngine>>>,
    pub outgoing: Arc<Mutex<VecDeque<EngineToIde>>>,
    pub connected: bool,
}

impl EditorConnection {
    /// Queue a message to send to the IDE.
    pub fn send(&self, msg: EngineToIde) {
        if let Ok(mut queue) = self.outgoing.lock() {
            queue.push_back(msg);
        }
    }
}

/// System: process incoming editor commands.
fn process_editor_messages(
    mut connection: ResMut<EditorConnection>,
    // These would be used to execute actual commands:
    // mut commands: Commands,
    // query: Query<...>,
) {
    let messages: Vec<IdeToEngine> = {
        if let Ok(mut incoming) = connection.incoming.lock() {
            incoming.drain(..).collect()
        } else {
            return;
        }
    };

    for msg in messages {
        match msg {
            IdeToEngine::Play => {
                log::info!("[Editor] Play requested");
            }
            IdeToEngine::Pause => {
                log::info!("[Editor] Pause requested");
            }
            IdeToEngine::Stop => {
                log::info!("[Editor] Stop requested");
            }
            IdeToEngine::ReloadScripts => {
                log::info!("[Editor] Script reload requested");
            }
            IdeToEngine::GetPerformanceStats => {
                connection.send(EngineToIde::PerformanceStats {
                    fps: 0.0, // TODO: read from diagnostics
                    entity_count: 0,
                    draw_calls: 0,
                });
            }
            IdeToEngine::ToggleDebug(enabled) => {
                log::info!("[Editor] Debug toggle: {}", enabled);
            }
            _ => {
                log::debug!("[Editor] Unhandled message: {:?}", msg);
            }
        }
    }
}
