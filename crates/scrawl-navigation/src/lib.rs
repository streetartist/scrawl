//! Scrawl Navigation - A* pathfinding and NavMesh.
//!
//! Provides grid-based A* pathfinding with support for generating
//! walkability grids from tilemap collision data.

use bevy::prelude::*;
use scrawl_core::schedule::ScrawlSet;
use std::collections::{BinaryHeap, HashMap};
use std::cmp::Ordering;

/// Navigation plugin.
pub struct ScrawlNavigationPlugin;

impl Plugin for ScrawlNavigationPlugin {
    fn build(&self, app: &mut App) {
        app.add_systems(Update, update_pathfinding.in_set(ScrawlSet::Navigation));
    }
}

/// A grid-based navigation map.
#[derive(Resource, Debug, Clone)]
pub struct NavGrid {
    pub width: usize,
    pub height: usize,
    pub cell_size: f32,
    /// true = walkable, false = blocked
    pub walkable: Vec<bool>,
}

impl NavGrid {
    pub fn new(width: usize, height: usize, cell_size: f32) -> Self {
        Self {
            width,
            height,
            cell_size,
            walkable: vec![true; width * height],
        }
    }

    pub fn set_blocked(&mut self, x: usize, y: usize, blocked: bool) {
        if x < self.width && y < self.height {
            self.walkable[y * self.width + x] = !blocked;
        }
    }

    pub fn is_walkable(&self, x: usize, y: usize) -> bool {
        if x >= self.width || y >= self.height {
            return false;
        }
        self.walkable[y * self.width + x]
    }

    /// Convert world position to grid coordinates.
    pub fn world_to_grid(&self, pos: Vec2) -> (usize, usize) {
        let x = (pos.x / self.cell_size).floor().max(0.0) as usize;
        let y = (pos.y / self.cell_size).floor().max(0.0) as usize;
        (x.min(self.width - 1), y.min(self.height - 1))
    }

    /// Convert grid coordinates to world position (center of cell).
    pub fn grid_to_world(&self, x: usize, y: usize) -> Vec2 {
        Vec2::new(
            x as f32 * self.cell_size + self.cell_size / 2.0,
            y as f32 * self.cell_size + self.cell_size / 2.0,
        )
    }

    /// A* pathfinding. Returns a list of world positions from start to goal.
    pub fn find_path(&self, start: Vec2, goal: Vec2) -> Option<Vec<Vec2>> {
        let (sx, sy) = self.world_to_grid(start);
        let (gx, gy) = self.world_to_grid(goal);

        if !self.is_walkable(gx, gy) {
            return None;
        }

        let start_node = (sx, sy);
        let goal_node = (gx, gy);

        let mut open = BinaryHeap::new();
        let mut came_from: HashMap<(usize, usize), (usize, usize)> = HashMap::new();
        let mut g_score: HashMap<(usize, usize), f32> = HashMap::new();

        g_score.insert(start_node, 0.0);
        open.push(AStarNode {
            pos: start_node,
            f_score: heuristic(start_node, goal_node),
        });

        let neighbors = [
            (-1i32, 0i32), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ];

        while let Some(current) = open.pop() {
            if current.pos == goal_node {
                // Reconstruct path
                let mut path = Vec::new();
                let mut node = goal_node;
                while node != start_node {
                    path.push(self.grid_to_world(node.0, node.1));
                    node = came_from[&node];
                }
                path.push(self.grid_to_world(start_node.0, start_node.1));
                path.reverse();
                return Some(path);
            }

            let current_g = g_score[&current.pos];

            for &(dx, dy) in &neighbors {
                let nx = current.pos.0 as i32 + dx;
                let ny = current.pos.1 as i32 + dy;
                if nx < 0 || ny < 0 {
                    continue;
                }
                let (nx, ny) = (nx as usize, ny as usize);
                if !self.is_walkable(nx, ny) {
                    continue;
                }

                let move_cost = if dx != 0 && dy != 0 { 1.414 } else { 1.0 };
                let tentative_g = current_g + move_cost;
                let neighbor = (nx, ny);

                if tentative_g < *g_score.get(&neighbor).unwrap_or(&f32::INFINITY) {
                    came_from.insert(neighbor, current.pos);
                    g_score.insert(neighbor, tentative_g);
                    open.push(AStarNode {
                        pos: neighbor,
                        f_score: tentative_g + heuristic(neighbor, goal_node),
                    });
                }
            }
        }

        None // No path found
    }
}

fn heuristic(a: (usize, usize), b: (usize, usize)) -> f32 {
    let dx = (a.0 as f32 - b.0 as f32).abs();
    let dy = (a.1 as f32 - b.1 as f32).abs();
    dx + dy // Manhattan distance
}

#[derive(Debug)]
struct AStarNode {
    pos: (usize, usize),
    f_score: f32,
}

impl PartialEq for AStarNode {
    fn eq(&self, other: &Self) -> bool {
        self.pos == other.pos
    }
}
impl Eq for AStarNode {}

impl Ord for AStarNode {
    fn cmp(&self, other: &Self) -> Ordering {
        other.f_score.partial_cmp(&self.f_score).unwrap_or(Ordering::Equal)
    }
}
impl PartialOrd for AStarNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Component: entity is following a path.
#[derive(Component)]
pub struct PathFollower {
    pub path: Vec<Vec2>,
    pub current_index: usize,
    pub speed: f32,
    pub finished: bool,
}

/// System: move PathFollower entities along their paths.
fn update_pathfinding(
    time: Res<Time>,
    mut query: Query<(&mut PathFollower, &mut scrawl_core::components::Transform2D)>,
) {
    let dt = time.delta_secs();

    for (mut follower, mut t2d) in query.iter_mut() {
        if follower.finished || follower.current_index >= follower.path.len() {
            follower.finished = true;
            continue;
        }

        let target = follower.path[follower.current_index];
        let dir = target - t2d.position;
        let dist = dir.length();

        if dist < 2.0 {
            follower.current_index += 1;
            if follower.current_index >= follower.path.len() {
                follower.finished = true;
            }
        } else {
            let move_dist = follower.speed * dt;
            t2d.position += dir.normalize() * move_dist.min(dist);
        }
    }
}
