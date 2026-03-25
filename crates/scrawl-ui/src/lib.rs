//! Scrawl UI - In-game UI system built on Bevy UI.
//!
//! Provides a simple API for creating buttons, labels, and health bars.

use bevy::prelude::*;

/// UI plugin.
pub struct ScrawlUIPlugin;

impl Plugin for ScrawlUIPlugin {
    fn build(&self, app: &mut App) {
        app.add_systems(Update, (update_buttons, update_health_bars));
    }
}

/// Marker for scrawl UI elements.
#[derive(Component)]
pub struct ScrawlUIElement;

/// A clickable button.
#[derive(Component)]
pub struct ScrawlButton {
    pub text: String,
    pub callback_id: String,
    pub hovered: bool,
    pub pressed: bool,
}

/// A text label.
#[derive(Component)]
pub struct ScrawlLabel {
    pub text: String,
}

/// A health/progress bar.
#[derive(Component)]
pub struct HealthBar {
    pub current: f32,
    pub max: f32,
    pub width: f32,
    pub height: f32,
    pub color: Color,
    pub background_color: Color,
}

impl Default for HealthBar {
    fn default() -> Self {
        Self {
            current: 100.0,
            max: 100.0,
            width: 200.0,
            height: 20.0,
            color: Color::srgb(0.2, 0.8, 0.2),
            background_color: Color::srgb(0.3, 0.3, 0.3),
        }
    }
}

/// Spawn a button in the UI.
pub fn spawn_button(
    commands: &mut Commands,
    text: &str,
    callback_id: &str,
    position: (f32, f32),
    size: (f32, f32),
) -> Entity {
    commands
        .spawn((
            ScrawlUIElement,
            ScrawlButton {
                text: text.to_string(),
                callback_id: callback_id.to_string(),
                hovered: false,
                pressed: false,
            },
            Button,
            Node {
                position_type: PositionType::Absolute,
                left: Val::Px(position.0),
                top: Val::Px(position.1),
                width: Val::Px(size.0),
                height: Val::Px(size.1),
                justify_content: JustifyContent::Center,
                align_items: AlignItems::Center,
                ..default()
            },
            BackgroundColor(Color::srgb(0.3, 0.3, 0.7)),
        ))
        .with_children(|parent| {
            parent.spawn((
                Text::new(text),
                TextFont { font_size: 16.0, ..default() },
                TextColor(Color::WHITE),
            ));
        })
        .id()
}

/// Spawn a text label in the UI.
pub fn spawn_label(
    commands: &mut Commands,
    text: &str,
    position: (f32, f32),
    font_size: f32,
    color: Color,
) -> Entity {
    commands
        .spawn((
            ScrawlUIElement,
            ScrawlLabel { text: text.to_string() },
            Text::new(text),
            TextFont { font_size, ..default() },
            TextColor(color),
            Node {
                position_type: PositionType::Absolute,
                left: Val::Px(position.0),
                top: Val::Px(position.1),
                ..default()
            },
        ))
        .id()
}

/// System: update button hover/press state.
fn update_buttons(
    mut query: Query<
        (&Interaction, &mut ScrawlButton, &mut BackgroundColor),
        Changed<Interaction>,
    >,
) {
    for (interaction, mut button, mut bg) in query.iter_mut() {
        match *interaction {
            Interaction::Pressed => {
                button.pressed = true;
                button.hovered = true;
                *bg = BackgroundColor(Color::srgb(0.2, 0.2, 0.5));
            }
            Interaction::Hovered => {
                button.pressed = false;
                button.hovered = true;
                *bg = BackgroundColor(Color::srgb(0.4, 0.4, 0.8));
            }
            Interaction::None => {
                button.pressed = false;
                button.hovered = false;
                *bg = BackgroundColor(Color::srgb(0.3, 0.3, 0.7));
            }
        }
    }
}

/// System: update health bar fill.
fn update_health_bars(
    query: Query<(&HealthBar, &Children), Changed<HealthBar>>,
    mut node_query: Query<&mut Node>,
) {
    for (bar, children) in query.iter() {
        let fraction = (bar.current / bar.max).clamp(0.0, 1.0);
        // The first child is the fill bar
        if let Some(child) = children.iter().next() {
            if let Ok(mut node) = node_query.get_mut(*child) {
                node.width = Val::Px(bar.width * fraction);
            }
        }
    }
}
