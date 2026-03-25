//! PyScene - Python wrapper for Scene entities.

use pyo3::prelude::*;

/// A Scene holds sprites and defines the background.
///
/// Usage from Python:
/// ```python
/// class MyScene(Scene):
///     def __init__(self):
///         super().__init__()
///         self.add_sprite(Ball())
/// ```
#[pyclass(name = "NativeScene")]
#[derive(Debug)]
pub struct PyScene {
    pub name: String,
    pub background_color: [f32; 4],
    pub background_image: Option<String>,
    pub sprites: Vec<Py<super::py_sprite::PySprite>>,
}

#[pymethods]
impl PyScene {
    #[new]
    #[pyo3(signature = (name="Scene"))]
    fn new(name: &str) -> Self {
        Self {
            name: name.to_string(),
            background_color: [1.0, 1.0, 1.0, 1.0],
            background_image: None,
            sprites: Vec::new(),
        }
    }

    /// Add a sprite to this scene.
    fn add_sprite(&mut self, sprite: Py<super::py_sprite::PySprite>) {
        self.sprites.push(sprite);
    }

    /// Set the background color.
    #[pyo3(signature = (r=255, g=255, b=255))]
    fn set_background_color(&mut self, r: u8, g: u8, b: u8) {
        self.background_color = [
            r as f32 / 255.0,
            g as f32 / 255.0,
            b as f32 / 255.0,
            1.0,
        ];
    }

    /// Set a background image.
    fn set_background_image(&mut self, path: &str) {
        self.background_image = Some(path.to_string());
    }

    /// Broadcast a message to all sprites.
    fn broadcast(&self, _event: &str) {
        // TODO: Send BroadcastEvent into the ECS world
        log::info!("Broadcast: {}", _event);
    }

    #[getter]
    fn name(&self) -> &str {
        &self.name
    }

    #[setter]
    fn set_name(&mut self, name: &str) {
        self.name = name.to_string();
    }
}
