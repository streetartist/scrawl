//! Python runtime hosting via PyO3.
//!
//! This module manages the embedded CPython interpreter:
//! - Initializes the Python runtime
//! - Loads user Python scripts
//! - Provides functions for the bridge to call Python generators
//! - Handles hot-reload of Python scripts

use pyo3::prelude::*;
use std::ffi::CString;
use std::path::Path;

/// Initialize the Python runtime. Call once at engine startup.
///
/// This sets up the Python interpreter and adds the scrawl package to sys.path.
pub fn initialize_python(scrawl_package_path: Option<&str>) -> PyResult<()> {
    pyo3::prepare_freethreaded_python();

    Python::with_gil(|py| {
        // Add scrawl package path to sys.path if provided
        if let Some(path) = scrawl_package_path {
            let sys = py.import("sys")?;
            let sys_path = sys.getattr("path")?;
            sys_path.call_method1("insert", (0, path))?;
        }

        log::info!("Python runtime initialized");
        Ok(())
    })
}

/// Load a Python script file and return the module.
pub fn load_script(path: &Path) -> PyResult<Py<PyModule>> {
    Python::with_gil(|py| {
        let code = std::fs::read_to_string(path)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        let module_name = path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("user_script");

        let code_c = CString::new(code).map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        let path_c = CString::new(path.to_str().unwrap_or("")).map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        let name_c = CString::new(module_name).map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        let module = PyModule::from_code(py, &code_c, &path_c, &name_c)?;

        Ok(module.into())
    })
}

/// Advance a Python generator (coroutine) by calling next().
///
/// Returns:
/// - Ok(Some(delay_ms)) if the generator yielded a delay value
/// - Ok(None) if the generator completed (StopIteration)
/// - Err if the generator raised an exception
pub fn advance_python_generator(generator: &Py<PyAny>) -> PyResult<Option<u64>> {
    Python::with_gil(|py| {
        let gen = generator.bind(py);
        match gen.call_method0("__next__") {
            Ok(result) => {
                // The yielded value is the delay in milliseconds
                if result.is_none() {
                    Ok(Some(0)) // yield None means continue next frame
                } else {
                    let delay: u64 = result.extract().unwrap_or(0);
                    Ok(Some(delay))
                }
            }
            Err(e) => {
                if e.is_instance_of::<pyo3::exceptions::PyStopIteration>(py) {
                    Ok(None) // Generator completed
                } else {
                    Err(e) // Real error
                }
            }
        }
    })
}

/// Scan a Python class for scrawl decorators and return handler info.
///
/// Looks for attributes like `_is_main`, `_key_event`, `_broadcast_event`, etc.
/// that are set by the @as_main, @on_key, @on_broadcast decorators.
pub fn scan_class_handlers(_py: Python<'_>, class: &Bound<'_, PyAny>) -> PyResult<Vec<HandlerInfo>> {
    let mut handlers = Vec::new();

    let dir = class.dir();
    for attr_name in dir.iter() {
        let name: String = attr_name.extract()?;
        if name.starts_with('_') && !name.starts_with("__") {
            continue; // Skip private attrs but not dunder
        }

        if let Ok(attr) = class.getattr(name.as_str()) {
            // Check for @as_main
            if attr.hasattr("_is_main").unwrap_or(false) {
                handlers.push(HandlerInfo {
                    method_name: name.clone(),
                    kind: HandlerKind::Main,
                });
            }

            // Check for @as_clones
            if attr.hasattr("_is_clones").unwrap_or(false) {
                handlers.push(HandlerInfo {
                    method_name: name.clone(),
                    kind: HandlerKind::Clone,
                });
            }

            // Check for @on_key
            if attr.hasattr("_key_event").unwrap_or(false) {
                if let Ok(key_event) = attr.getattr("_key_event") {
                    let tuple: (String, String) = key_event.extract()?;
                    handlers.push(HandlerInfo {
                        method_name: name.clone(),
                        kind: HandlerKind::Key {
                            key: tuple.0,
                            mode: tuple.1,
                        },
                    });
                }
            }

            // Check for @on_broadcast
            if attr.hasattr("_broadcast_event").unwrap_or(false) {
                if let Ok(event) = attr.getattr("_broadcast_event") {
                    let event_name: String = event.extract()?;
                    handlers.push(HandlerInfo {
                        method_name: name.clone(),
                        kind: HandlerKind::Broadcast {
                            event: event_name,
                        },
                    });
                }
            }

            // Check for @on_sprite_clicked
            if attr.hasattr("_is_sprite_clicked").unwrap_or(false) {
                handlers.push(HandlerInfo {
                    method_name: name.clone(),
                    kind: HandlerKind::SpriteClicked,
                });
            }

            // Check for @on_edge_collision
            if attr.hasattr("_edge_collision").unwrap_or(false) {
                if let Ok(edge) = attr.getattr("_edge_collision") {
                    let edge_name: String = edge.extract()?;
                    handlers.push(HandlerInfo {
                        method_name: name.clone(),
                        kind: HandlerKind::EdgeCollision { edge: edge_name },
                    });
                }
            }

            // Check for @on_sprite_collision
            if attr.hasattr("_sprite_collision").unwrap_or(false) {
                if let Ok(target) = attr.getattr("_sprite_collision") {
                    let target_name: String = target.extract()?;
                    handlers.push(HandlerInfo {
                        method_name: name.clone(),
                        kind: HandlerKind::SpriteCollision {
                            target: target_name,
                        },
                    });
                }
            }

            // Check for @on_mouse
            if attr.hasattr("_mouse_event").unwrap_or(false) {
                if let Ok(mouse_event) = attr.getattr("_mouse_event") {
                    let tuple: (u32, String) = mouse_event.extract()?;
                    handlers.push(HandlerInfo {
                        method_name: name.clone(),
                        kind: HandlerKind::Mouse {
                            button: tuple.0,
                            mode: tuple.1,
                        },
                    });
                }
            }
        }
    }

    Ok(handlers)
}

/// Information about a discovered handler method.
#[derive(Debug, Clone)]
pub struct HandlerInfo {
    pub method_name: String,
    pub kind: HandlerKind,
}

/// The kind of event handler.
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
