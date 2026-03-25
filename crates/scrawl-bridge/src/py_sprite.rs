//! PySprite / PyPhysicsSprite - Python wrappers for sprite entities.
//!
//! These are proxy objects: they buffer property changes and commands,
//! which are flushed into the ECS world each frame by the bridge.

use pyo3::prelude::*;

/// Base sprite class exposed to Python.
///
/// Usage:
/// ```python
/// class Ball(Sprite):
///     def __init__(self):
///         super().__init__()
///         self.name = "Ball"
///         self.add_costume("ball", "ball.png")
/// ```
#[pyclass(name = "NativeSprite", subclass)]
#[derive(Debug, Clone)]
pub struct PySprite {
    // Identity
    pub name: String,

    // Transform
    pub x: f32,
    pub y: f32,
    pub direction: f32,
    pub size: f32,

    // Appearance
    pub visible: bool,
    pub color: [f32; 3],
    pub costumes: Vec<(String, String)>, // (name, path)
    pub current_costume: usize,

    // Pen
    pub pen_down: bool,
    pub pen_color: [f32; 3],
    pub pen_size: f32,

    // Collision
    pub collision_type: String,

    // ECS binding (set when spawned into the engine)
    pub entity_id: Option<u64>,
}

#[pymethods]
impl PySprite {
    #[new]
    fn new() -> Self {
        Self {
            name: "Sprite".to_string(),
            x: 400.0,
            y: 300.0,
            direction: 90.0,
            size: 1.0,
            visible: true,
            color: [1.0, 0.4, 0.4],
            costumes: Vec::new(),
            current_costume: 0,
            pen_down: false,
            pen_color: [0.0, 0.0, 0.0],
            pen_size: 2.0,
            collision_type: "rect".to_string(),
            entity_id: None,
        }
    }

    // ========================================================================
    // Movement
    // ========================================================================

    /// Move in the current direction by `steps` pixels.
    fn r#move(&mut self, steps: f32) {
        let rad = (self.direction - 90.0_f32).to_radians();
        self.x += rad.cos() * steps;
        self.y -= rad.sin() * steps;
    }

    /// Move up by pixels.
    fn move_up(&mut self, steps: f32) {
        self.y -= steps;
    }

    /// Move down by pixels.
    fn move_down(&mut self, steps: f32) {
        self.y += steps;
    }

    /// Move left by pixels.
    fn move_left(&mut self, steps: f32) {
        self.x -= steps;
    }

    /// Move right by pixels.
    fn move_right(&mut self, steps: f32) {
        self.x += steps;
    }

    /// Turn left by degrees.
    fn turn_left(&mut self, degrees: f32) {
        self.direction -= degrees;
    }

    /// Turn right by degrees.
    fn turn_right(&mut self, degrees: f32) {
        self.direction += degrees;
    }

    /// Go to a position.
    fn go_to(&mut self, x: f32, y: f32) {
        self.x = x;
        self.y = y;
    }

    /// Point towards a position.
    fn point_towards_position(&mut self, x: f32, y: f32) {
        let dx = x - self.x;
        let dy = y - self.y;
        self.direction = dy.atan2(dx).to_degrees() + 90.0;
    }

    // ========================================================================
    // Appearance
    // ========================================================================

    /// Add a costume from image path.
    fn add_costume(&mut self, name: &str, path: &str) {
        self.costumes.push((name.to_string(), path.to_string()));
    }

    /// Switch to a costume by name.
    fn switch_costume(&mut self, name: &str) {
        if let Some(idx) = self.costumes.iter().position(|(n, _)| n == name) {
            self.current_costume = idx;
        }
    }

    /// Switch to the next costume.
    fn next_costume(&mut self) {
        if !self.costumes.is_empty() {
            self.current_costume = (self.current_costume + 1) % self.costumes.len();
        }
    }

    /// Show the sprite.
    fn show(&mut self) {
        self.visible = true;
    }

    /// Hide the sprite.
    fn hide(&mut self) {
        self.visible = false;
    }

    /// Say something (speech bubble).
    #[pyo3(signature = (text, duration=2000))]
    fn say(&self, text: &str, duration: u32) {
        // TODO: Send command to ECS to add SpeechBubble component
        log::debug!("{} says: {} ({}ms)", self.name, text, duration);
    }

    // ========================================================================
    // Pen
    // ========================================================================

    fn pen_down_cmd(&mut self) {
        self.pen_down = true;
    }

    fn pen_up_cmd(&mut self) {
        self.pen_down = false;
    }

    fn set_pen_color(&mut self, r: u8, g: u8, b: u8) {
        self.pen_color = [r as f32 / 255.0, g as f32 / 255.0, b as f32 / 255.0];
    }

    fn set_pen_size(&mut self, size: f32) {
        self.pen_size = size;
    }

    // ========================================================================
    // Properties
    // ========================================================================

    #[getter]
    fn get_name(&self) -> &str {
        &self.name
    }

    #[setter]
    fn set_name(&mut self, name: &str) {
        self.name = name.to_string();
    }

    #[getter]
    fn get_x(&self) -> f32 {
        self.x
    }

    #[setter]
    fn set_x(&mut self, x: f32) {
        self.x = x;
    }

    #[getter]
    fn get_y(&self) -> f32 {
        self.y
    }

    #[setter]
    fn set_y(&mut self, y: f32) {
        self.y = y;
    }

    #[getter]
    fn get_direction(&self) -> f32 {
        self.direction
    }

    #[setter]
    fn set_direction(&mut self, direction: f32) {
        self.direction = direction;
    }

    #[getter]
    fn get_size(&self) -> f32 {
        self.size
    }

    #[setter]
    fn set_size(&mut self, size: f32) {
        self.size = size;
    }

    #[getter]
    fn get_visible(&self) -> bool {
        self.visible
    }

    #[setter]
    fn set_visible(&mut self, visible: bool) {
        self.visible = visible;
    }

    #[getter]
    fn get_collision_type(&self) -> &str {
        &self.collision_type
    }

    #[setter]
    fn set_collision_type(&mut self, t: &str) {
        self.collision_type = t.to_string();
    }
}

/// Physics sprite with velocity, gravity, etc.
#[pyclass(name = "NativePhysicsSprite", extends = PySprite)]
#[derive(Debug, Clone)]
pub struct PyPhysicsSprite {
    pub velocity_x: f32,
    pub velocity_y: f32,
    pub gravity: f32,
    pub friction: f32,
    pub elasticity: f32,
    pub angular_velocity: f32,
}

#[pymethods]
impl PyPhysicsSprite {
    #[new]
    fn new() -> (Self, PySprite) {
        (
            Self {
                velocity_x: 0.0,
                velocity_y: 0.0,
                gravity: 0.5,
                friction: 0.02,
                elasticity: 0.8,
                angular_velocity: 0.0,
            },
            PySprite::new(),
        )
    }

    #[getter]
    fn get_velocity_x(&self) -> f32 {
        self.velocity_x
    }

    #[setter]
    fn set_velocity_x(&mut self, vx: f32) {
        self.velocity_x = vx;
    }

    #[getter]
    fn get_velocity_y(&self) -> f32 {
        self.velocity_y
    }

    #[setter]
    fn set_velocity_y(&mut self, vy: f32) {
        self.velocity_y = vy;
    }

    #[getter]
    fn get_gravity(&self) -> f32 {
        self.gravity
    }

    #[setter]
    fn set_gravity(&mut self, g: f32) {
        self.gravity = g;
    }

    #[getter]
    fn get_friction(&self) -> f32 {
        self.friction
    }

    #[setter]
    fn set_friction(&mut self, f: f32) {
        self.friction = f;
    }

    #[getter]
    fn get_elasticity(&self) -> f32 {
        self.elasticity
    }

    #[setter]
    fn set_elasticity(&mut self, e: f32) {
        self.elasticity = e;
    }
}
