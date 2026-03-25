//! Scrawl Tilemap - Tile-based map rendering and collision.
//!
//! Built on bevy_ecs_tilemap for efficient GPU-accelerated tile rendering.

use bevy::prelude::*;
use bevy_ecs_tilemap::prelude::*;
use scrawl_core::schedule::ScrawlSet;

/// Tilemap plugin.
pub struct ScrawlTilemapPlugin;

impl Plugin for ScrawlTilemapPlugin {
    fn build(&self, app: &mut App) {
        app.add_plugins(TilemapPlugin);
        app.add_systems(Update, update_tilemap_collisions.in_set(ScrawlSet::Physics));
    }
}

/// Configuration for a scrawl tilemap layer.
#[derive(Component)]
pub struct ScrawlTilemap {
    /// Tile size in pixels.
    pub tile_size: Vec2,
    /// Map size in tiles.
    pub map_size: UVec2,
    /// Path to the tileset image.
    pub tileset_path: String,
    /// Tile data: row-major, each u32 is a tile index (0 = empty).
    pub tiles: Vec<u32>,
    /// Which tile indices are solid (for collision).
    pub solid_tiles: Vec<u32>,
}

/// Marker for collision layer entities generated from tilemap.
#[derive(Component)]
pub struct TilemapCollisionLayer;

/// System: generate collision shapes from tilemap solid tiles.
/// Runs once when ScrawlTilemap is added.
fn update_tilemap_collisions(
    query: Query<&ScrawlTilemap, Added<ScrawlTilemap>>,
) {
    for tilemap in query.iter() {
        // TODO: Generate collider shapes from solid_tiles
        // This will create AABB colliders for contiguous solid tile regions
        log::info!(
            "Tilemap collision generation: {}x{}, {} solid tile types",
            tilemap.map_size.x,
            tilemap.map_size.y,
            tilemap.solid_tiles.len()
        );
    }
}

/// Helper to create a tilemap from a 2D array of tile indices.
pub fn create_tilemap(
    commands: &mut Commands,
    asset_server: &AssetServer,
    config: &ScrawlTilemap,
) -> Entity {
    let texture_handle: Handle<Image> = asset_server.load(&config.tileset_path);

    let map_size = TilemapSize {
        x: config.map_size.x,
        y: config.map_size.y,
    };
    let tile_size = TilemapTileSize {
        x: config.tile_size.x,
        y: config.tile_size.y,
    };
    let grid_size = tile_size.into();

    let tilemap_entity = commands.spawn_empty().id();
    let mut tile_storage = TileStorage::empty(map_size);

    for y in 0..map_size.y {
        for x in 0..map_size.x {
            let idx = (y * map_size.x + x) as usize;
            let tile_idx = if idx < config.tiles.len() {
                config.tiles[idx]
            } else {
                0
            };

            if tile_idx == 0 {
                continue; // Empty tile
            }

            let tile_pos = TilePos { x, y };
            let tile_entity = commands
                .spawn(TileBundle {
                    position: tile_pos,
                    tilemap_id: TilemapId(tilemap_entity),
                    texture_index: TileTextureIndex(tile_idx),
                    ..default()
                })
                .id();
            tile_storage.set(&tile_pos, tile_entity);
        }
    }

    let map_type = TilemapType::Square;

    commands.entity(tilemap_entity).insert(TilemapBundle {
        grid_size,
        map_type,
        size: map_size,
        storage: tile_storage,
        texture: TilemapTexture::Single(texture_handle),
        tile_size,
        transform: Transform::default(),
        ..default()
    });

    tilemap_entity
}
