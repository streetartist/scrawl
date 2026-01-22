"""
Scrawl IDE Main Window

The main application window with dock-based layout.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QToolBar, QMenuBar, QMenu,
    QStatusBar, QFileDialog, QMessageBox, QWidget, QVBoxLayout,
    QTabWidget, QTextEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon, QActionGroup

from .settings import Settings
from .project import Project
from .i18n import Translator, tr
from panels.scene_editor import SceneView, SceneToolbar
from panels.scene_tree import HierarchyView
from panels.inspector import PropertyEditor
from panels.code_editor import CodeEditorWidget
from panels.asset_browser import AssetTreeView, AssetPreview
from models import ProjectModel, SceneModel, SpriteModel
from runner import GameRunner


class MainWindow(QMainWindow):
    """Main IDE window with dock-based panel layout."""

    def __init__(self):
        super().__init__()

        self.settings = Settings()
        self.project = Project(self)
        self.game_runner = GameRunner(self)
        self.translator = Translator()

        # Initialize language from settings
        saved_language = self.settings.get_language()
        self.translator.set_language(saved_language)

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_docks()
        self._setup_connections()
        self._restore_state()

    def _setup_ui(self):
        """Initialize the main UI components."""
        self.setWindowTitle(tr("app.name"))
        self.setMinimumSize(1200, 800)

        # Central widget - Scene Editor
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        self.scene_toolbar = SceneToolbar()
        self.scene_view = SceneView()

        central_layout.addWidget(self.scene_toolbar)
        central_layout.addWidget(self.scene_view)

        self.setCentralWidget(central_widget)

        # Status bar
        self.statusBar().showMessage(tr("status.ready"))

    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu(tr("menu.file"))

        new_action = QAction(tr("menu.file.new"), self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_action)

        open_action = QAction(tr("menu.file.open"), self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction(tr("menu.file.save"), self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        save_as_action = QAction(tr("menu.file.save_as"), self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction(tr("menu.file.exit"), self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu(tr("menu.edit"))

        undo_action = QAction(tr("menu.edit.undo"), self)
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction(tr("menu.edit.redo"), self)
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(tr("menu.edit.cut"), self)
        cut_action.setShortcut(QKeySequence.Cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction(tr("menu.edit.copy"), self)
        copy_action.setShortcut(QKeySequence.Copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction(tr("menu.edit.paste"), self)
        paste_action.setShortcut(QKeySequence.Paste)
        edit_menu.addAction(paste_action)

        # View menu
        view_menu = menubar.addMenu(tr("menu.view"))
        self._view_menu = view_menu  # Store for dock toggle actions

        # Language submenu
        language_menu = view_menu.addMenu(tr("menu.view.language"))
        language_group = QActionGroup(self)
        language_group.setExclusive(True)

        for lang_code, lang_name in self.translator.get_languages().items():
            lang_action = QAction(lang_name, self)
            lang_action.setCheckable(True)
            lang_action.setData(lang_code)
            if lang_code == self.translator.current_language:
                lang_action.setChecked(True)
            lang_action.triggered.connect(lambda checked, code=lang_code: self._on_language_changed(code))
            language_group.addAction(lang_action)
            language_menu.addAction(lang_action)

        view_menu.addSeparator()

        # Scene menu
        scene_menu = menubar.addMenu(tr("menu.scene"))

        add_sprite_action = QAction(tr("menu.scene.add_sprite"), self)
        add_sprite_action.triggered.connect(self._on_add_sprite)
        scene_menu.addAction(add_sprite_action)

        add_scene_action = QAction(tr("menu.scene.add_scene"), self)
        add_scene_action.triggered.connect(self._on_add_scene)
        scene_menu.addAction(add_scene_action)

        # Run menu
        run_menu = menubar.addMenu(tr("menu.run"))

        run_action = QAction(tr("menu.run.run"), self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self._on_run_game)
        run_menu.addAction(run_action)

        stop_action = QAction(tr("menu.run.stop"), self)
        stop_action.setShortcut("Shift+F5")
        stop_action.triggered.connect(self._on_stop_game)
        run_menu.addAction(stop_action)

        # Help menu
        help_menu = menubar.addMenu(tr("menu.help"))

        about_action = QAction(tr("menu.help.about"), self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        """Set up the main toolbar."""
        toolbar = QToolBar(tr("toolbar.main"))
        toolbar.setObjectName("MainToolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # New project
        new_btn = QAction(tr("toolbar.new"), self)
        new_btn.setToolTip(tr("toolbar.new.tip"))
        new_btn.triggered.connect(self._on_new_project)
        toolbar.addAction(new_btn)

        # Open project
        open_btn = QAction(tr("toolbar.open"), self)
        open_btn.setToolTip(tr("toolbar.open.tip"))
        open_btn.triggered.connect(self._on_open_project)
        toolbar.addAction(open_btn)

        # Save
        save_btn = QAction(tr("toolbar.save"), self)
        save_btn.setToolTip(tr("toolbar.save.tip"))
        save_btn.triggered.connect(self._on_save)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        # Run game
        run_btn = QAction(tr("toolbar.run"), self)
        run_btn.setToolTip(tr("toolbar.run.tip"))
        run_btn.triggered.connect(self._on_run_game)
        toolbar.addAction(run_btn)

        # Stop game
        stop_btn = QAction(tr("toolbar.stop"), self)
        stop_btn.setToolTip(tr("toolbar.stop.tip"))
        stop_btn.triggered.connect(self._on_stop_game)
        toolbar.addAction(stop_btn)

    def _setup_docks(self):
        """Set up the dock widgets."""
        # Scene Tree (left)
        self.hierarchy_dock = QDockWidget(tr("dock.scene_tree"), self)
        self.hierarchy_dock.setObjectName("SceneTreeDock")
        self.hierarchy_view = HierarchyView()
        self.hierarchy_dock.setWidget(self.hierarchy_view)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.hierarchy_dock)
        self._view_menu.addAction(self.hierarchy_dock.toggleViewAction())

        # Inspector (right)
        self.inspector_dock = QDockWidget(tr("dock.inspector"), self)
        self.inspector_dock.setObjectName("InspectorDock")
        self.property_editor = PropertyEditor()
        self.inspector_dock.setWidget(self.property_editor)
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector_dock)
        self._view_menu.addAction(self.inspector_dock.toggleViewAction())

        # Code Editor (bottom)
        self.code_dock = QDockWidget(tr("dock.code_editor"), self)
        self.code_dock.setObjectName("CodeEditorDock")
        self.code_tabs = QTabWidget()
        self.code_tabs.setTabsClosable(True)
        self.code_tabs.tabCloseRequested.connect(self._on_close_code_tab)
        self.code_dock.setWidget(self.code_tabs)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.code_dock)
        self._view_menu.addAction(self.code_dock.toggleViewAction())

        # Console (bottom, tabbed with code editor)
        self.console_dock = QDockWidget(tr("dock.console"), self)
        self.console_dock.setObjectName("ConsoleDock")
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(self.console_output.font())
        self.console_dock.setWidget(self.console_output)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)
        self.tabifyDockWidget(self.code_dock, self.console_dock)
        self._view_menu.addAction(self.console_dock.toggleViewAction())

        # Asset Browser (bottom)
        self.asset_dock = QDockWidget(tr("dock.asset_browser"), self)
        self.asset_dock.setObjectName("AssetBrowserDock")
        asset_widget = QWidget()
        asset_layout = QVBoxLayout(asset_widget)
        asset_layout.setContentsMargins(0, 0, 0, 0)

        self.asset_tree = AssetTreeView()
        self.asset_preview = AssetPreview()

        asset_layout.addWidget(self.asset_tree, 2)
        asset_layout.addWidget(self.asset_preview, 1)

        self.asset_dock.setWidget(asset_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.asset_dock)
        self.tabifyDockWidget(self.console_dock, self.asset_dock)
        self._view_menu.addAction(self.asset_dock.toggleViewAction())

        # Show code dock by default
        self.code_dock.raise_()

    def _setup_connections(self):
        """Set up signal connections."""
        # Project signals
        self.project.project_loaded.connect(self._on_project_loaded)
        self.project.project_modified.connect(self._update_title)

        # Scene view signals
        self.scene_view.sprite_selected.connect(self._on_sprite_selected)
        self.scene_view.sprite_moved.connect(self._on_sprite_moved)

        # Hierarchy view signals
        self.hierarchy_view.sprite_selected.connect(self._on_hierarchy_sprite_selected)
        self.hierarchy_view.sprite_double_clicked.connect(self._on_sprite_double_clicked)

        # Property editor signals
        self.property_editor.property_changed.connect(self._on_property_changed)

        # Asset browser signals
        self.asset_tree.file_selected.connect(self._on_asset_selected)
        self.asset_tree.file_double_clicked.connect(self._on_asset_double_clicked)

        # Game runner signals
        self.game_runner.output_received.connect(self._on_game_output)
        self.game_runner.game_started.connect(self._on_game_started)
        self.game_runner.game_stopped.connect(self._on_game_stopped)

        # Language change listener
        self.translator.add_language_listener(self._on_language_applied)

    def _restore_state(self):
        """Restore window state from settings."""
        geometry = self.settings.load_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)

        state = self.settings.load_window_state()
        if state:
            self.restoreState(state)

    def _update_title(self):
        """Update the window title."""
        title = tr("app.name")
        if self.project.model:
            title = f"{self.project.model.name} - {tr('app.name')}"
            if self.project.is_modified:
                title = f"*{title}"
        self.setWindowTitle(title)

    def _on_language_changed(self, language_code: str):
        """Handle language change from menu."""
        self.settings.set_language(language_code)
        self.translator.set_language(language_code)

    def _on_language_applied(self, language: str):
        """Handle language applied - show restart message."""
        QMessageBox.information(
            self,
            tr("app.name"),
            "Language changed. Please restart the application for changes to take full effect.\n"
            "语言已更改。请重新启动应用程序以使更改完全生效。"
        )

    # Menu actions
    def _on_new_project(self):
        """Create a new project."""
        path, _ = QFileDialog.getSaveFileName(
            self, tr("dialog.new_project"), "",
            tr("dialog.project_filter")
        )
        if path:
            if not path.endswith('.scrawl'):
                path += '.scrawl'
            name = os.path.splitext(os.path.basename(path))[0]
            self.project.new_project(path, name)

    def _on_open_project(self):
        """Open an existing project."""
        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.open_project"), "",
            tr("dialog.project_filter")
        )
        if path:
            self.project.open_project(path)

    def _on_save(self):
        """Save the current project."""
        if self.project.path:
            self.project.save()
        else:
            self._on_save_as()

    def _on_save_as(self):
        """Save the project to a new location."""
        path, _ = QFileDialog.getSaveFileName(
            self, tr("dialog.save_project"), "",
            tr("dialog.project_filter")
        )
        if path:
            if not path.endswith('.scrawl'):
                path += '.scrawl'
            self.project.save_as(path)

    def _on_add_sprite(self):
        """Add a new sprite to the current scene."""
        if not self.project.model:
            return

        sprite = SpriteModel.create_default("NewSprite")
        if self.project.model.scenes:
            self.project.model.scenes[0].sprites.append(sprite)
            self.scene_view.add_sprite(sprite)
            self.hierarchy_view.refresh()
            self.project.mark_modified()

    def _on_add_scene(self):
        """Add a new scene to the project."""
        if not self.project.model:
            return

        scene = SceneModel.create_default(f"Scene{len(self.project.model.scenes) + 1}")
        self.project.model.scenes.append(scene)
        self.hierarchy_view.refresh()
        self.project.mark_modified()

    def _on_run_game(self):
        """Run the game."""
        if self.project.model and self.project.path:
            self.console_output.clear()
            self.game_runner.run(self.project)

    def _on_stop_game(self):
        """Stop the running game."""
        self.game_runner.stop()

    def _on_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self, tr("app.about.title"),
            tr("app.about.text")
        )

    # Event handlers
    def _on_project_loaded(self, model: ProjectModel):
        """Handle project loaded."""
        self._update_title()

        # Update scene view
        self.scene_view.clear()
        if model.scenes:
            for sprite in model.scenes[0].sprites:
                self.scene_view.add_sprite(sprite)

        # Update hierarchy
        self.hierarchy_view.set_project(model)

        # Update asset browser
        if self.project.project_dir:
            self.asset_tree.set_root_path(self.project.project_dir)

        self.statusBar().showMessage(tr("status.opened").format(path=self.project.path))

    def _on_sprite_selected(self, sprite: SpriteModel):
        """Handle sprite selection in scene view."""
        self.property_editor.set_sprite(sprite)
        self.hierarchy_view.select_sprite(sprite)

    def _on_sprite_moved(self, sprite: SpriteModel, x: float, y: float):
        """Handle sprite movement in scene view."""
        sprite.x = x
        sprite.y = y
        self.property_editor.refresh()
        self.project.mark_modified()

    def _on_hierarchy_sprite_selected(self, sprite: SpriteModel):
        """Handle sprite selection in hierarchy."""
        self.scene_view.select_sprite(sprite)
        self.property_editor.set_sprite(sprite)

    def _on_sprite_double_clicked(self, sprite: SpriteModel):
        """Handle sprite double-click to open script."""
        if sprite.script_path:
            self._open_script(sprite.script_path)

    def _on_property_changed(self, sprite: SpriteModel, prop: str, value):
        """Handle property change in inspector."""
        self.scene_view.update_sprite(sprite)
        self.project.mark_modified()

    def _on_asset_selected(self, path: str):
        """Handle asset selection."""
        self.asset_preview.preview(path)

    def _on_asset_double_clicked(self, path: str):
        """Handle asset double-click."""
        if path.endswith('.py'):
            self._open_script(path)
        elif path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            # Could drag to scene
            pass

    def _on_close_code_tab(self, index: int):
        """Close a code editor tab."""
        self.code_tabs.removeTab(index)

    def _on_game_output(self, text: str):
        """Handle game output."""
        self.console_output.append(text)

    def _on_game_started(self):
        """Handle game started."""
        self.statusBar().showMessage(tr("status.game_running"))
        self.console_dock.raise_()

    def _on_game_stopped(self):
        """Handle game stopped."""
        self.statusBar().showMessage(tr("status.game_stopped"))

    def _open_script(self, path: str):
        """Open a script in the code editor."""
        # Check if already open
        for i in range(self.code_tabs.count()):
            widget = self.code_tabs.widget(i)
            if hasattr(widget, 'file_path') and widget.file_path == path:
                self.code_tabs.setCurrentIndex(i)
                return

        # Create new editor
        editor = CodeEditorWidget()
        editor.open_file(path)
        name = os.path.basename(path)
        self.code_tabs.addTab(editor, name)
        self.code_tabs.setCurrentWidget(editor)
        self.code_dock.raise_()

    def closeEvent(self, event):
        """Handle window close."""
        # Check for unsaved changes
        if self.project.is_modified:
            reply = QMessageBox.question(
                self, tr("dialog.unsaved_title"),
                tr("dialog.unsaved_message"),
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                self._on_save()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        # Save window state
        self.settings.save_window_geometry(self.saveGeometry())
        self.settings.save_window_state(self.saveState())

        # Stop game if running
        self.game_runner.stop()

        event.accept()
