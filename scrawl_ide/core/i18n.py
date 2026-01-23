"""
Scrawl IDE Internationalization (i18n) System

Provides bilingual support (Chinese/English) with Chinese as default.
"""

from typing import Dict, Optional, Callable, List


class Translator:
    """Translation manager for the application."""

    _instance: Optional['Translator'] = None
    _initialized: bool = False

    # Supported languages
    CHINESE = "zh_CN"
    ENGLISH = "en_US"
    DEFAULT = CHINESE

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if Translator._initialized:
            return
        Translator._initialized = True

        self._current_language = self.DEFAULT
        self._translations: Dict[str, Dict[str, str]] = {}
        self._listeners: List[Callable[[str], None]] = []
        self._load_translations()

    def _load_translations(self):
        """Load all translation dictionaries."""
        self._translations = {
            self.CHINESE: TRANSLATIONS_ZH,
            self.ENGLISH: TRANSLATIONS_EN
        }

    @property
    def current_language(self) -> str:
        return self._current_language

    def set_language(self, language: str):
        """Set the current language."""
        if language in self._translations:
            self._current_language = language
            # Notify listeners
            for listener in self._listeners:
                listener(language)

    def add_language_listener(self, callback: Callable[[str], None]):
        """Add a callback for language changes."""
        self._listeners.append(callback)

    def remove_language_listener(self, callback: Callable[[str], None]):
        """Remove a language change callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get_languages(self) -> Dict[str, str]:
        """Get available languages with display names."""
        return {
            self.CHINESE: "中文",
            self.ENGLISH: "English"
        }

    def tr(self, key: str) -> str:
        """Translate a key to the current language."""
        translations = self._translations.get(self._current_language, {})
        return translations.get(key, key)


def tr(key: str) -> str:
    """Shortcut function for translation."""
    return Translator().tr(key)


# =============================================================================
# Chinese Translations (Default)
# =============================================================================
TRANSLATIONS_ZH = {
    # Application
    "app.name": "Scrawl IDE",
    "app.about.title": "关于 Scrawl IDE",
    "app.about.text": "Scrawl IDE v0.2.1\n\n一个用于 Scrawl 游戏引擎的可视化 IDE。\n\n作者: UESTC streetartist\n基于 PySide6 构建。",

    # Menu - File
    "menu.file": "文件(&F)",
    "menu.file.new": "新建项目(&N)...",
    "menu.file.open": "打开项目(&O)...",
    "menu.file.save": "保存(&S)",
    "menu.file.save_as": "另存为(&A)...",
    "menu.file.exit": "退出(&X)",

    # Menu - Edit
    "menu.edit": "编辑(&E)",
    "menu.edit.undo": "撤销(&U)",
    "menu.edit.redo": "重做(&R)",
    "menu.edit.cut": "剪切(&T)",
    "menu.edit.copy": "复制(&C)",
    "menu.edit.paste": "粘贴(&P)",

    # Menu - View
    "menu.view": "视图(&V)",
    "menu.view.language": "语言(&L)",
    "menu.view.reset_layout": "重置布局(&R)",

    # Menu - Scene
    "menu.scene": "场景(&S)",
    "menu.scene.add_sprite": "添加精灵(&S)",
    "menu.scene.add_scene": "添加场景(&C)",

    # Menu - Run
    "menu.run": "运行(&R)",
    "menu.run.run": "运行游戏(&R)",
    "menu.run.stop": "停止(&S)",

    # Menu - Help
    "menu.help": "帮助(&H)",
    "menu.help.about": "关于(&A)",

    # Toolbar
    "toolbar.main": "主工具栏",
    "toolbar.new": "新建",
    "toolbar.open": "打开",
    "toolbar.save": "保存",
    "toolbar.run": "运行",
    "toolbar.stop": "停止",
    "toolbar.new.tip": "新建项目 (Ctrl+N)",
    "toolbar.open.tip": "打开项目 (Ctrl+O)",
    "toolbar.save.tip": "保存 (Ctrl+S)",
    "toolbar.run.tip": "运行游戏 (F5)",
    "toolbar.stop.tip": "停止游戏 (Shift+F5)",

    # Dock panels
    "dock.scene_tree": "场景树",
    "dock.inspector": "属性检查器",
    "dock.code_editor": "代码编辑器",
    "dock.console": "控制台",
    "dock.asset_browser": "资源浏览器",

    # Scene toolbar
    "scene.toolbar.select": "选择",
    "scene.toolbar.pan": "平移",
    "scene.toolbar.zoom": "缩放:",
    "scene.toolbar.grid": "网格",
    "scene.toolbar.snap": "吸附",
    "scene.toolbar.grid_size": "网格大小:",
    "scene.toolbar.fit": "适应",
    "scene.toolbar.select.tip": "选择和移动精灵 (V)",
    "scene.toolbar.pan.tip": "平移视图 (H)",

    # Inspector
    "inspector.no_selection": "未选中任何对象",
    "inspector.identity": "标识",
    "inspector.name": "名称:",
    "inspector.class": "类名:",
    "inspector.transform": "变换",
    "inspector.position": "位置:",
    "inspector.direction": "方向:",
    "inspector.size": "大小:",
    "inspector.appearance": "外观",
    "inspector.visible": "可见:",
    "inspector.costumes": "造型:",
    "inspector.default_costume": "默认造型:",
    "inspector.add_costume": "添加造型...",
    "inspector.rename_costume": "重命名造型",
    "inspector.rename_costume_prompt": "新名称:",
    "inspector.costume_name": "造型名称",
    "inspector.costume_name_prompt": "输入造型名称:",
    "inspector.set_as_default": "设为默认",
    "inspector.delete_costume": "删除造型",
    "inspector.game_settings": "游戏设置",
    "inspector.game_info": "游戏信息",
    "inspector.game_title": "游戏标题:",
    "inspector.resolution": "分辨率",
    "inspector.width": "宽度:",
    "inspector.height": "高度:",
    "inspector.fullscreen": "全屏:",
    "inspector.runtime": "运行时",
    "inspector.fps": "帧率 (FPS):",
    "inspector.debug": "调试模式:",

    # Collision
    "inspector.collision": "碰撞",
    "inspector.collision_type": "碰撞类型:",

    # Physics
    "inspector.physics": "物理",
    "inspector.is_physics": "物理精灵:",
    "inspector.gravity": "重力:",
    "inspector.friction": "摩擦力:",
    "inspector.elasticity": "弹性:",

    # Background
    "inspector.background": "背景",
    "inspector.bg_color": "背景颜色:",
    "inspector.bg_image": "背景图片:",
    "inspector.no_bg_image": "无背景图片",

    # Hierarchy
    "hierarchy.header": "场景树",
    "hierarchy.add_scene": "添加场景",
    "hierarchy.add_sprite": "添加精灵",
    "hierarchy.rename": "重命名",
    "hierarchy.duplicate": "复制",
    "hierarchy.delete_scene": "删除场景",
    "hierarchy.delete_sprite": "删除精灵",
    "hierarchy.cannot_delete": "无法删除",
    "hierarchy.cannot_delete_last": "无法删除最后一个场景。",
    "hierarchy.confirm_delete_scene": "删除场景 '{name}'?",
    "hierarchy.confirm_delete_sprite": "删除精灵 '{name}'?",

    # Asset browser
    "asset.new_script": "新建 Python 脚本...",
    "asset.new_folder": "新建文件夹...",
    "asset.rename": "重命名...",
    "asset.delete": "删除",
    "asset.reveal": "在资源管理器中显示",
    "asset.new_file_title": "新建文件",
    "asset.new_file_prompt": "文件名:",
    "asset.new_folder_title": "新建文件夹",
    "asset.new_folder_prompt": "文件夹名:",
    "asset.rename_title": "重命名",
    "asset.rename_prompt": "新名称:",
    "asset.exists_error": "'{name}' 已存在。",
    "asset.delete_confirm": "删除{type} '{name}'?",
    "asset.type_file": "文件",
    "asset.type_folder": "文件夹",
    "asset.preview_empty": "选择资源以预览",
    "asset.preview_unavailable": "无法预览 {ext} 文件",
    "asset.audio_unavailable": "音频预览不可用\n(未安装 QMultimedia)",

    # Dialogs
    "dialog.new_project": "新建项目",
    "dialog.open_project": "打开项目",
    "dialog.save_project": "保存项目",
    "dialog.project_filter": "Scrawl 项目 (*.scrawl)",
    "dialog.image_filter": "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.svg)",
    "dialog.python_filter": "Python 文件 (*.py)",
    "dialog.unsaved_title": "未保存的更改",
    "dialog.unsaved_message": "是否在关闭前保存更改?",
    "dialog.error": "错误",
    "dialog.add_sprite_title": "添加精灵",
    "dialog.add_sprite_prompt": "精灵名称:",
    "dialog.add_scene_title": "添加场景",
    "dialog.add_scene_prompt": "场景名称:",
    "dialog.select_costume": "添加造型",
    "dialog.select_script": "选择脚本",
    "dialog.select_bg_image": "选择背景图片",
    "dialog.no_project": "请先创建或打开一个项目。",
    "dialog.no_scene": "请先选择一个场景。",

    # Status messages
    "status.ready": "就绪",
    "status.opened": "已打开: {path}",
    "status.game_running": "游戏运行中...",
    "status.game_stopped": "游戏已停止",

    # Game runner
    "runner.already_running": "游戏已在运行中。\n",
    "runner.no_project": "未加载项目。\n",
    "runner.generated": "已生成游戏代码: {path}\n",
    "runner.debug_mode": "以调试模式运行...\n",
    "runner.started": "游戏已启动。\n",
    "runner.start_failed": "启动游戏进程失败。\n",
    "runner.error": "运行游戏出错: {error}\n",
    "runner.stopping": "正在停止游戏...\n",
    "runner.exited": "\n游戏已退出，退出代码: {code}。\n",
    "runner.process_error": "进程错误: {error}\n",

    # Code editor
    "editor.could_not_open": "无法打开文件: {error}",
    "editor.could_not_save": "无法保存文件: {error}",

    # Settings dialog
    "menu.edit.settings": "设置(&S)...",
    "dialog.settings.title": "设置",
    "dialog.settings.editor": "编辑器",
    "dialog.settings.font_family": "字体:",
    "dialog.settings.font_size": "字号:",
    "dialog.settings.preview": "预览:",
    "dialog.settings.ai": "AI 助手",
    "dialog.settings.ai_key": "API Key:",
    "dialog.settings.ai_endpoint": "端点:",
    "dialog.settings.ai_model": "模型:",

    # AI Chat
    "dock.ai_chat": "AI 助手",
    "ai.input_placeholder": "输入消息，让 AI 帮助你编写代码...",
    "ai.send": "发送",
    "ai.apply": "应用",
    "ai.clear": "清空",
}


# =============================================================================
# English Translations
# =============================================================================
TRANSLATIONS_EN = {
    # Application
    "app.name": "Scrawl IDE",
    "app.about.title": "About Scrawl IDE",
    "app.about.text": "Scrawl IDE v0.2.1\n\nA visual IDE for the Scrawl game engine.\n\nAuthor: UESTC streetartist\nBuilt with PySide6.",

    # Menu - File
    "menu.file": "&File",
    "menu.file.new": "&New Project...",
    "menu.file.open": "&Open Project...",
    "menu.file.save": "&Save",
    "menu.file.save_as": "Save &As...",
    "menu.file.exit": "E&xit",

    # Menu - Edit
    "menu.edit": "&Edit",
    "menu.edit.undo": "&Undo",
    "menu.edit.redo": "&Redo",
    "menu.edit.cut": "Cu&t",
    "menu.edit.copy": "&Copy",
    "menu.edit.paste": "&Paste",

    # Menu - View
    "menu.view": "&View",
    "menu.view.language": "&Language",
    "menu.view.reset_layout": "&Reset Layout",

    # Menu - Scene
    "menu.scene": "&Scene",
    "menu.scene.add_sprite": "Add &Sprite",
    "menu.scene.add_scene": "Add S&cene",

    # Menu - Run
    "menu.run": "&Run",
    "menu.run.run": "&Run Game",
    "menu.run.stop": "&Stop",

    # Menu - Help
    "menu.help": "&Help",
    "menu.help.about": "&About",

    # Toolbar
    "toolbar.main": "Main Toolbar",
    "toolbar.new": "New",
    "toolbar.open": "Open",
    "toolbar.save": "Save",
    "toolbar.run": "Run",
    "toolbar.stop": "Stop",
    "toolbar.new.tip": "New Project (Ctrl+N)",
    "toolbar.open.tip": "Open Project (Ctrl+O)",
    "toolbar.save.tip": "Save (Ctrl+S)",
    "toolbar.run.tip": "Run Game (F5)",
    "toolbar.stop.tip": "Stop Game (Shift+F5)",

    # Dock panels
    "dock.scene_tree": "Scene Tree",
    "dock.inspector": "Inspector",
    "dock.code_editor": "Code Editor",
    "dock.console": "Console",
    "dock.asset_browser": "Asset Browser",

    # Scene toolbar
    "scene.toolbar.select": "Select",
    "scene.toolbar.pan": "Pan",
    "scene.toolbar.zoom": "Zoom:",
    "scene.toolbar.grid": "Grid",
    "scene.toolbar.snap": "Snap",
    "scene.toolbar.grid_size": "Grid Size:",
    "scene.toolbar.fit": "Fit",
    "scene.toolbar.select.tip": "Select and move sprites (V)",
    "scene.toolbar.pan.tip": "Pan the view (H)",

    # Inspector
    "inspector.no_selection": "No Selection",
    "inspector.identity": "Identity",
    "inspector.name": "Name:",
    "inspector.class": "Class:",
    "inspector.transform": "Transform",
    "inspector.position": "Position:",
    "inspector.direction": "Direction:",
    "inspector.size": "Size:",
    "inspector.appearance": "Appearance",
    "inspector.visible": "Visible:",
    "inspector.costumes": "Costumes:",
    "inspector.default_costume": "Default Costume:",
    "inspector.add_costume": "Add Costume...",
    "inspector.rename_costume": "Rename Costume",
    "inspector.rename_costume_prompt": "New name:",
    "inspector.costume_name": "Costume Name",
    "inspector.costume_name_prompt": "Enter costume name:",
    "inspector.set_as_default": "Set as Default",
    "inspector.delete_costume": "Delete Costume",
    "inspector.game_settings": "Game Settings",
    "inspector.game_info": "Game Info",
    "inspector.game_title": "Game Title:",
    "inspector.resolution": "Resolution",
    "inspector.width": "Width:",
    "inspector.height": "Height:",
    "inspector.fullscreen": "Fullscreen:",
    "inspector.runtime": "Runtime",
    "inspector.fps": "Frame Rate (FPS):",
    "inspector.debug": "Debug Mode:",

    # Collision
    "inspector.collision": "Collision",
    "inspector.collision_type": "Collision Type:",

    # Physics
    "inspector.physics": "Physics",
    "inspector.is_physics": "Physics Sprite:",
    "inspector.gravity": "Gravity:",
    "inspector.friction": "Friction:",
    "inspector.elasticity": "Elasticity:",

    # Background
    "inspector.background": "Background",
    "inspector.bg_color": "Background Color:",
    "inspector.bg_image": "Background Image:",
    "inspector.no_bg_image": "No background image",

    # Hierarchy
    "hierarchy.header": "Scene Tree",
    "hierarchy.add_scene": "Add Scene",
    "hierarchy.add_sprite": "Add Sprite",
    "hierarchy.rename": "Rename",
    "hierarchy.duplicate": "Duplicate",
    "hierarchy.delete_scene": "Delete Scene",
    "hierarchy.delete_sprite": "Delete Sprite",
    "hierarchy.cannot_delete": "Cannot Delete",
    "hierarchy.cannot_delete_last": "Cannot delete the last scene.",
    "hierarchy.confirm_delete_scene": "Delete scene '{name}'?",
    "hierarchy.confirm_delete_sprite": "Delete sprite '{name}'?",

    # Asset browser
    "asset.new_script": "New Python Script...",
    "asset.new_folder": "New Folder...",
    "asset.rename": "Rename...",
    "asset.delete": "Delete",
    "asset.reveal": "Reveal in Explorer",
    "asset.new_file_title": "New File",
    "asset.new_file_prompt": "File name:",
    "asset.new_folder_title": "New Folder",
    "asset.new_folder_prompt": "Folder name:",
    "asset.rename_title": "Rename",
    "asset.rename_prompt": "New name:",
    "asset.exists_error": "'{name}' already exists.",
    "asset.delete_confirm": "Delete {type} '{name}'?",
    "asset.type_file": "file",
    "asset.type_folder": "folder",
    "asset.preview_empty": "Select an asset to preview",
    "asset.preview_unavailable": "No preview for {ext} files",
    "asset.audio_unavailable": "Audio preview not available\n(QMultimedia not installed)",

    # Dialogs
    "dialog.new_project": "New Project",
    "dialog.open_project": "Open Project",
    "dialog.save_project": "Save Project As",
    "dialog.project_filter": "Scrawl Project (*.scrawl)",
    "dialog.image_filter": "Images (*.png *.jpg *.jpeg *.gif *.bmp *.svg)",
    "dialog.python_filter": "Python Files (*.py)",
    "dialog.unsaved_title": "Unsaved Changes",
    "dialog.unsaved_message": "Do you want to save changes before closing?",
    "dialog.error": "Error",
    "dialog.add_sprite_title": "Add Sprite",
    "dialog.add_sprite_prompt": "Sprite name:",
    "dialog.add_scene_title": "Add Scene",
    "dialog.add_scene_prompt": "Scene name:",
    "dialog.select_costume": "Add Costume",
    "dialog.select_script": "Select Script",
    "dialog.select_bg_image": "Select Background Image",
    "dialog.no_project": "Please create or open a project first.",
    "dialog.no_scene": "Please select a scene first.",

    # Status messages
    "status.ready": "Ready",
    "status.opened": "Opened: {path}",
    "status.game_running": "Game running...",
    "status.game_stopped": "Game stopped",

    # Game runner
    "runner.already_running": "Game is already running.\n",
    "runner.no_project": "No project loaded.\n",
    "runner.generated": "Generated game code: {path}\n",
    "runner.debug_mode": "Running in debug mode...\n",
    "runner.started": "Game started.\n",
    "runner.start_failed": "Failed to start game process.\n",
    "runner.error": "Error running game: {error}\n",
    "runner.stopping": "Stopping game...\n",
    "runner.exited": "\nGame exited with code {code}.\n",
    "runner.process_error": "Process error: {error}\n",

    # Code editor
    "editor.could_not_open": "Could not open file: {error}",
    "editor.could_not_save": "Could not save file: {error}",

    # Settings dialog
    "menu.edit.settings": "&Settings...",
    "dialog.settings.title": "Settings",
    "dialog.settings.editor": "Editor",
    "dialog.settings.font_family": "Font:",
    "dialog.settings.font_size": "Font Size:",
    "dialog.settings.preview": "Preview:",
    "dialog.settings.ai": "AI Assistant",
    "dialog.settings.ai_key": "API Key:",
    "dialog.settings.ai_endpoint": "Endpoint:",
    "dialog.settings.ai_model": "Model:",

    # AI Chat
    "dock.ai_chat": "AI Assistant",
    "ai.input_placeholder": "Type a message to get AI help with your code...",
    "ai.send": "Send",
    "ai.apply": "Apply",
    "ai.clear": "Clear",
}
