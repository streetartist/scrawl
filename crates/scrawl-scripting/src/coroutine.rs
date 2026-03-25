//! Coroutine scheduler for yield-based game scripts.
//!
//! This module implements the generator/coroutine pattern from scrawl v1,
//! where script handlers are Python generators that yield wait times in ms.
//!
//! Each entity can have multiple active coroutines (main task, key handlers, etc.).
//! The scheduler advances them each frame, respecting their yield delays.

use bevy::prelude::*;
use std::collections::HashMap;
use std::time::{Duration, Instant};

/// A single coroutine task tracked by the scheduler.
#[derive(Debug)]
pub struct CoroutineTask {
    /// The entity this coroutine belongs to.
    pub entity: Entity,
    /// Unique ID for this coroutine instance.
    pub task_id: u64,
    /// The type of coroutine (main, key handler, broadcast, etc.).
    pub kind: CoroutineKind,
    /// When this coroutine should next be advanced (None = ready now).
    pub wake_at: Option<Instant>,
    /// Whether this coroutine has completed (returned StopIteration).
    pub completed: bool,
    /// Python-side: the generator object ID. Rust-side: unused.
    pub python_generator_id: Option<u64>,
}

/// What kind of coroutine this is.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CoroutineKind {
    Main,
    Clone,
    KeyHandler { key: String, mode: String },
    BroadcastHandler { event: String },
    MouseHandler { button: u32, mode: String },
    SpriteClicked,
    EdgeCollision { edge: String },
    SpriteCollision { target: String },
}

/// Resource that manages all active coroutines across all entities.
#[derive(Resource, Debug, Default)]
pub struct CoroutineScheduler {
    /// All active coroutines, keyed by task_id.
    pub tasks: HashMap<u64, CoroutineTask>,
    /// Next task ID to assign.
    next_id: u64,
}

impl CoroutineScheduler {
    /// Register a new coroutine and return its task ID.
    pub fn add_task(&mut self, entity: Entity, kind: CoroutineKind) -> u64 {
        let id = self.next_id;
        self.next_id += 1;

        self.tasks.insert(
            id,
            CoroutineTask {
                entity,
                task_id: id,
                kind,
                wake_at: None,
                completed: false,
                python_generator_id: None,
            },
        );

        id
    }

    /// Mark a coroutine as waiting for `delay_ms` milliseconds.
    pub fn set_delay(&mut self, task_id: u64, delay_ms: u64) {
        if let Some(task) = self.tasks.get_mut(&task_id) {
            task.wake_at = Some(Instant::now() + Duration::from_millis(delay_ms));
        }
    }

    /// Mark a coroutine as completed.
    pub fn complete_task(&mut self, task_id: u64) {
        if let Some(task) = self.tasks.get_mut(&task_id) {
            task.completed = true;
        }
    }

    /// Get all task IDs that are ready to run (not waiting, not completed).
    pub fn ready_tasks(&self) -> Vec<u64> {
        let now = Instant::now();
        self.tasks
            .values()
            .filter(|t| {
                !t.completed && t.wake_at.map_or(true, |wake| now >= wake)
            })
            .map(|t| t.task_id)
            .collect()
    }

    /// Remove all completed tasks.
    pub fn cleanup_completed(&mut self) {
        self.tasks.retain(|_, t| !t.completed);
    }

    /// Remove all tasks for a specific entity.
    pub fn remove_entity_tasks(&mut self, entity: Entity) {
        self.tasks.retain(|_, t| t.entity != entity);
    }
}

/// System that advances coroutines each frame.
///
/// For Rust scripts, this is a no-op (Rust scripts use on_update directly).
/// For Python scripts, the actual advancement happens in the bridge via PyO3.
/// This system just handles cleanup and scheduling bookkeeping.
pub fn advance_coroutines(mut scheduler: ResMut<CoroutineScheduler>) {
    scheduler.cleanup_completed();
}
