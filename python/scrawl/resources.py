"""
资源管理器 - 参考 Godot ResourceLoader。

提供统一的资源加载和缓存机制。

用法:
    # 预加载
    ResourceLoader.preload("player_sprite", "sprites/player.png")
    ResourceLoader.preload("jump_sfx", "sounds/jump.wav")

    # 使用
    sprite.texture = ResourceLoader.load("sprites/player.png")
"""

from typing import Dict, Optional, Any, Set
import os


class Resource:
    """资源基类 - 参考 Godot Resource。"""

    def __init__(self, path: str = ""):
        self.path = path
        self._name = ""

    @property
    def resource_name(self) -> str:
        return self._name or os.path.basename(self.path)

    @resource_name.setter
    def resource_name(self, value: str):
        self._name = value


class ImageTexture(Resource):
    """图片纹理资源。"""

    def __init__(self, path: str = ""):
        super().__init__(path)
        self.width = 0
        self.height = 0
        self._loaded = False

    def is_loaded(self) -> bool:
        return self._loaded


class AudioResource(Resource):
    """音频资源。"""

    def __init__(self, path: str = ""):
        super().__init__(path)
        self.duration = 0.0
        self.loop = False


class FontResource(Resource):
    """字体资源。"""

    def __init__(self, path: str = "", size: int = 16):
        super().__init__(path)
        self.size = size


class ResourceLoader:
    """全局资源加载器 - 参考 Godot ResourceLoader。"""

    _cache: Dict[str, Resource] = {}
    _search_paths: list = ["."]

    @classmethod
    def load(cls, path: str, type_hint: str = "") -> Optional[Resource]:
        """加载资源（带缓存）。"""
        if path in cls._cache:
            return cls._cache[path]

        resource = cls._create_resource(path, type_hint)
        if resource:
            cls._cache[path] = resource
        return resource

    @classmethod
    def preload(cls, name: str, path: str, type_hint: str = "") -> Optional[Resource]:
        """预加载资源。"""
        resource = cls.load(path, type_hint)
        if resource:
            resource.resource_name = name
        return resource

    @classmethod
    def exists(cls, path: str) -> bool:
        """检查资源是否存在。"""
        for base in cls._search_paths:
            full = os.path.join(base, path)
            if os.path.exists(full):
                return True
        return path in cls._cache

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()

    @classmethod
    def add_search_path(cls, path: str):
        if path not in cls._search_paths:
            cls._search_paths.append(path)

    @classmethod
    def _create_resource(cls, path: str, type_hint: str = "") -> Optional[Resource]:
        ext = os.path.splitext(path)[1].lower()

        if type_hint == "texture" or ext in ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.svg'):
            return ImageTexture(path)
        elif type_hint == "audio" or ext in ('.wav', '.ogg', '.mp3', '.flac'):
            return AudioResource(path)
        elif type_hint == "font" or ext in ('.ttf', '.otf', '.woff'):
            return FontResource(path)
        else:
            return Resource(path)

    @classmethod
    def get_cached_resources(cls) -> Dict[str, Resource]:
        return dict(cls._cache)
