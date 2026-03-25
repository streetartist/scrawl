//! Input handling systems.
//!
//! - `gather_input` (Update): captures pressed/released into InputBuffer
//! - `dispatch_input_events` (FixedUpdate): drains buffer + generates held events from KeyState

use bevy::prelude::*;

use crate::events::{InputMode, KeyInputEvent, MouseInputEvent};
use crate::resources::{InputBuffer, KeyState, MouseState};

/// System (Update): capture one-shot input (pressed/released) into the buffer.
/// Held events are NOT buffered — they're generated in FixedUpdate from KeyState.
pub fn gather_input(
    keyboard: Res<ButtonInput<KeyCode>>,
    mouse_buttons: Res<ButtonInput<MouseButton>>,
    windows: Query<&Window>,
    mut key_state: ResMut<KeyState>,
    mut mouse_state: ResMut<MouseState>,
    mut buffer: ResMut<InputBuffer>,
) {
    for key in keyboard.get_just_pressed() {
        key_state.held_keys.insert(*key);
        buffer.key_events.push((*key, InputMode::Pressed));
    }

    for key in keyboard.get_just_released() {
        key_state.held_keys.remove(key);
        buffer.key_events.push((*key, InputMode::Released));
    }

    // Mouse position
    if let Ok(window) = windows.get_single() {
        if let Some(pos) = window.cursor_position() {
            mouse_state.position = pos;
        }
    }

    for btn in [MouseButton::Left, MouseButton::Middle, MouseButton::Right] {
        if mouse_buttons.just_pressed(btn) {
            buffer.mouse_events.push((btn, InputMode::Pressed, mouse_state.position));
        }
        if mouse_buttons.just_released(btn) {
            buffer.mouse_events.push((btn, InputMode::Released, mouse_state.position));
        }
    }
}

/// System (FixedUpdate): drain buffered pressed/released + generate held events.
pub fn dispatch_input_events(
    mut buffer: ResMut<InputBuffer>,
    key_state: Res<KeyState>,
    mouse_state: Res<MouseState>,
    mouse_buttons: Res<ButtonInput<MouseButton>>,
    mut key_events: EventWriter<KeyInputEvent>,
    mut mouse_events: EventWriter<MouseInputEvent>,
) {
    // Drain one-shot events from buffer
    for (key, mode) in buffer.key_events.drain(..) {
        key_events.send(KeyInputEvent { key, mode });
    }
    for (button, mode, position) in buffer.mouse_events.drain(..) {
        mouse_events.send(MouseInputEvent { button, mode, position });
    }

    // Generate held events directly from current state (once per fixed tick)
    for key in key_state.held_keys.iter() {
        key_events.send(KeyInputEvent {
            key: *key,
            mode: InputMode::Held,
        });
    }

    for btn in [MouseButton::Left, MouseButton::Middle, MouseButton::Right] {
        if mouse_buttons.pressed(btn) {
            mouse_events.send(MouseInputEvent {
                button: btn,
                mode: InputMode::Held,
                position: mouse_state.position,
            });
        }
    }
}
