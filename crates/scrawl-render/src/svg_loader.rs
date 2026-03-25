//! Custom SVG asset loader using resvg.
//! Renders SVG files to RGBA pixel data and loads them as Bevy Image assets.

use bevy::asset::io::Reader;
use bevy::asset::{AssetLoader, LoadContext};
use bevy::prelude::*;

/// Plugin that registers the SVG asset loader.
pub struct SvgLoaderPlugin;

impl Plugin for SvgLoaderPlugin {
    fn build(&self, app: &mut App) {
        app.register_asset_loader(SvgAssetLoader);
    }
}

struct SvgAssetLoader;

impl AssetLoader for SvgAssetLoader {
    type Asset = Image;
    type Settings = ();
    type Error = SvgLoadError;

    fn load(
        &self,
        reader: &mut dyn Reader,
        _settings: &Self::Settings,
        _load_context: &mut LoadContext,
    ) -> impl std::future::Future<Output = Result<Self::Asset, Self::Error>> + Send {
        async move {
            let mut bytes = Vec::new();
            reader
                .read_to_end(&mut bytes)
                .await
                .map_err(|e| SvgLoadError::Io(e.to_string()))?;

            // Fix broken Scratch SVGs: replace fill="undefined" with fill="none"
            let svg_str = String::from_utf8_lossy(&bytes);
            let fixed = svg_str
                .replace("fill=\"undefined\"", "fill=\"none\"")
                .replace("fill='undefined'", "fill='none'")
                .replace("stroke=\"undefined\"", "stroke=\"none\"")
                .replace("stroke='undefined'", "stroke='none'");
            let bytes = fixed.into_bytes();

            let tree = resvg::usvg::Tree::from_data(&bytes, &resvg::usvg::Options::default())
                .map_err(|e| SvgLoadError::Parse(e.to_string()))?;

            let size = tree.size();
            let width = size.width().ceil() as u32;
            let height = size.height().ceil() as u32;

            if width == 0 || height == 0 {
                return Err(SvgLoadError::Parse("SVG has zero size".into()));
            }

            let mut pixmap = resvg::tiny_skia::Pixmap::new(width, height)
                .ok_or_else(|| SvgLoadError::Parse("Failed to create pixmap".into()))?;

            resvg::render(&tree, resvg::tiny_skia::Transform::default(), &mut pixmap.as_mut());

            // Convert from premultiplied RGBA to straight RGBA
            let mut data = pixmap.data().to_vec();
            for pixel in data.chunks_exact_mut(4) {
                let a = pixel[3] as u16;
                if a > 0 && a < 255 {
                    pixel[0] = ((pixel[0] as u16 * 255) / a).min(255) as u8;
                    pixel[1] = ((pixel[1] as u16 * 255) / a).min(255) as u8;
                    pixel[2] = ((pixel[2] as u16 * 255) / a).min(255) as u8;
                }
            }

            let image = Image::new(
                bevy::render::render_resource::Extent3d {
                    width,
                    height,
                    depth_or_array_layers: 1,
                },
                bevy::render::render_resource::TextureDimension::D2,
                data,
                bevy::render::render_resource::TextureFormat::Rgba8UnormSrgb,
                bevy::render::render_asset::RenderAssetUsages::RENDER_WORLD
                    | bevy::render::render_asset::RenderAssetUsages::MAIN_WORLD,
            );

            Ok(image)
        }
    }

    fn extensions(&self) -> &[&str] {
        &["svg"]
    }
}

#[derive(Debug, thiserror::Error)]
pub enum SvgLoadError {
    #[error("IO error: {0}")]
    Io(String),
    #[error("SVG parse error: {0}")]
    Parse(String),
}
