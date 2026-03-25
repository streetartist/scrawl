//! Pen drawing system.
//!
//! Renders accumulated pen paths as line segments using Bevy's Gizmos.
//! In the future this could be upgraded to a mesh-based renderer for persistence.

use bevy::prelude::*;
use scrawl_core::components::PenState;

/// Draws pen paths using Bevy gizmos (immediate-mode, redrawn each frame).
pub fn update_pen_paths(mut gizmos: Gizmos, query: Query<&PenState>) {
    for pen in query.iter() {
        if pen.path.len() < 2 {
            continue;
        }
        let color = pen.color;
        for window in pen.path.windows(2) {
            gizmos.line_2d(window[0], window[1], color);
        }
    }
}
