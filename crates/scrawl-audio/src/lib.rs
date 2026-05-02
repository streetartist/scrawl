//! Scrawl Audio - Sound effects, music, and audio bus system.
//!
//! Built on bevy_kira_audio for high-quality audio playback.

use bevy::prelude::*;
use bevy_kira_audio::prelude::*;

/// Audio plugin wrapping bevy_kira_audio.
pub struct ScrawlAudioPlugin;

impl Plugin for ScrawlAudioPlugin {
    fn build(&self, app: &mut App) {
        app.add_plugins(AudioPlugin);
        app.init_resource::<AudioManager>();
    }
}

/// High-level audio manager resource.
///
/// Provides a simple API matching scrawl v1:
/// ```ignore
/// audio.play_sound("explosion.ogg");
/// audio.play_music("bgm.ogg");
/// audio.set_music_volume(0.5);
/// ```
#[derive(Resource)]
pub struct AudioManager {
    pub music_volume: f64,
    pub sound_volume: f64,
    music_instance: Option<Handle<AudioInstance>>,
}

impl Default for AudioManager {
    fn default() -> Self {
        Self {
            music_volume: 1.0,
            sound_volume: 1.0,
            music_instance: None,
        }
    }
}

impl AudioManager {
    /// Play a one-shot sound effect.
    pub fn play_sound(
        &self,
        audio: &Audio,
        asset_server: &AssetServer,
        path: &str,
    ) {
        let handle = asset_server.load(path);
        audio.play(handle).with_volume(self.sound_volume);
    }

    /// Play background music (looping). Stops any current music.
    pub fn play_music(
        &mut self,
        audio: &Audio,
        asset_server: &AssetServer,
        looped: bool,
        path: &str,
    ) {
        self.music_instance = None;
        let handle: Handle<bevy_kira_audio::AudioSource> = asset_server.load(path);
        let instance = if looped {
            audio
                .play(handle)
                .looped()
                .with_volume(self.music_volume)
                .handle()
        } else {
            audio
                .play(handle)
                .with_volume(self.music_volume)
                .handle()
        };
        self.music_instance = Some(instance);
    }

    /// Stop background music.
    pub fn stop_music(&mut self, audio_instances: &mut Assets<AudioInstance>) {
        if let Some(handle) = self.music_instance.take() {
            if let Some(instance) = audio_instances.get_mut(&handle) {
                instance.stop(AudioTween::default());
            }
        }
    }

    /// Pause background music.
    pub fn pause_music(&self, audio_instances: &mut Assets<AudioInstance>) {
        if let Some(handle) = &self.music_instance {
            if let Some(instance) = audio_instances.get_mut(handle) {
                instance.pause(AudioTween::default());
            }
        }
    }

    /// Resume background music.
    pub fn resume_music(&self, audio_instances: &mut Assets<AudioInstance>) {
        if let Some(handle) = &self.music_instance {
            if let Some(instance) = audio_instances.get_mut(handle) {
                instance.resume(AudioTween::default());
            }
        }
    }

    /// Set music volume (0.0 - 1.0).
    pub fn set_music_volume(&mut self, volume: f64) {
        self.music_volume = volume.clamp(0.0, 1.0);
    }

    /// Set sound effects volume (0.0 - 1.0).
    pub fn set_sound_volume(&mut self, volume: f64) {
        self.sound_volume = volume.clamp(0.0, 1.0);
    }
}

/// Component for entities that emit spatial audio (future use).
#[derive(Component)]
pub struct SpatialAudioSource {
    pub sound_path: String,
    pub volume: f64,
    pub max_distance: f32,
}
