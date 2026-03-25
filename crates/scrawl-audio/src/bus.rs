//! Audio bus system - named buses with independent volume control.
//!
//! Three built-in buses: **Master**, **SFX**, and **Music**.
//! Every bus stores a volume multiplier (0.0–1.0). The effective volume of a
//! sound played on a bus equals `bus_volume * master_volume`.

use bevy::prelude::*;
use std::collections::HashMap;

/// Well-known bus names.
pub const BUS_MASTER: &str = "master";
pub const BUS_SFX: &str = "sfx";
pub const BUS_MUSIC: &str = "music";

/// A single audio bus with a name and a volume level.
#[derive(Debug, Clone)]
pub struct AudioBus {
    /// Human-readable name (e.g. "sfx", "music").
    pub name: String,
    /// Volume multiplier in 0.0–1.0.
    pub volume: f64,
    /// Whether the bus is muted (volume forced to 0 regardless of `volume`).
    pub muted: bool,
}

impl AudioBus {
    pub fn new(name: impl Into<String>, volume: f64) -> Self {
        Self {
            name: name.into(),
            volume: volume.clamp(0.0, 1.0),
            muted: false,
        }
    }

    /// Effective volume taking mute into account.
    pub fn effective_volume(&self) -> f64 {
        if self.muted {
            0.0
        } else {
            self.volume
        }
    }
}

/// Resource that holds all named audio buses.
///
/// The **master** bus acts as a global multiplier: the final volume for any bus
/// is `bus.effective_volume() * master.effective_volume()`.
#[derive(Resource, Debug)]
pub struct AudioBusController {
    buses: HashMap<String, AudioBus>,
}

impl Default for AudioBusController {
    fn default() -> Self {
        let mut buses = HashMap::new();
        buses.insert(BUS_MASTER.to_string(), AudioBus::new(BUS_MASTER, 1.0));
        buses.insert(BUS_SFX.to_string(), AudioBus::new(BUS_SFX, 1.0));
        buses.insert(BUS_MUSIC.to_string(), AudioBus::new(BUS_MUSIC, 1.0));
        Self { buses }
    }
}

impl AudioBusController {
    /// Get a bus by name (read-only).
    pub fn get(&self, name: &str) -> Option<&AudioBus> {
        self.buses.get(name)
    }

    /// Get a bus by name (mutable).
    pub fn get_mut(&mut self, name: &str) -> Option<&mut AudioBus> {
        self.buses.get_mut(name)
    }

    /// Add (or replace) a custom bus.
    pub fn add_bus(&mut self, name: impl Into<String>, volume: f64) {
        let name = name.into();
        self.buses.insert(name.clone(), AudioBus::new(name, volume));
    }

    /// Set volume for a specific bus. Returns `false` if the bus doesn't exist.
    pub fn set_volume(&mut self, name: &str, volume: f64) -> bool {
        if let Some(bus) = self.buses.get_mut(name) {
            bus.volume = volume.clamp(0.0, 1.0);
            true
        } else {
            false
        }
    }

    /// Mute / unmute a bus.
    pub fn set_muted(&mut self, name: &str, muted: bool) -> bool {
        if let Some(bus) = self.buses.get_mut(name) {
            bus.muted = muted;
            true
        } else {
            false
        }
    }

    /// Compute the final volume for a bus, multiplied by the master bus.
    pub fn final_volume(&self, name: &str) -> f64 {
        let master = self
            .buses
            .get(BUS_MASTER)
            .map_or(1.0, |b| b.effective_volume());
        let bus = self
            .buses
            .get(name)
            .map_or(1.0, |b| b.effective_volume());
        master * bus
    }

    /// Iterator over all bus names.
    pub fn bus_names(&self) -> impl Iterator<Item = &str> {
        self.buses.keys().map(|s| s.as_str())
    }
}
