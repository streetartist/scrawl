//! Scrawl Bridge - PyO3 cdylib exposing the Scrawl engine to Python
//!
//! This crate compiles to `scrawl_native.pyd` (Windows) or `scrawl_native.so` (Linux/macOS).
//! It provides the Python classes: ScrawlBridge, PyGame, PyScene, PySprite.
//!
//! The bridge acts as a proxy between Python objects and the Bevy ECS World.

mod py_game;
pub mod runtime;

use pyo3::prelude::*;

/// The Python module entry point.
#[pymodule]
fn scrawl_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<py_game::PyGame>()?;

    // Version info
    m.add("__version__", "2.2.0")?;
    m.add("ENGINE_NAME", "Scrawl Engine (Bevy)")?;

    Ok(())
}
