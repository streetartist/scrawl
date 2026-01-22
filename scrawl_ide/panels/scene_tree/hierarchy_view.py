"""
Hierarchy View

Tree view showing the scene hierarchy (scenes and sprites).
"""

from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QMenu, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from typing import Optional, Dict

from models import ProjectModel, SceneModel, SpriteModel
from core.i18n import tr


class HierarchyView(QTreeWidget):
    """Tree view showing project hierarchy."""

    sprite_selected = Signal(object)  # SpriteModel
    sprite_double_clicked = Signal(object)  # SpriteModel
    scene_selected = Signal(object)  # SceneModel
    item_renamed = Signal(object, str)  # model, new_name

    def __init__(self, parent=None):
        super().__init__(parent)

        self._project: Optional[ProjectModel] = None
        self._sprite_items: Dict[str, QTreeWidgetItem] = {}
        self._scene_items: Dict[str, QTreeWidgetItem] = {}

        self._setup_ui()

    def _setup_ui(self):
        """Set up the tree view."""
        self.setHeaderLabel(tr("hierarchy.header"))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setSelectionMode(QTreeWidget.SingleSelection)

        # Connect signals
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)

    def set_project(self, project: ProjectModel):
        """Set the project to display."""
        self._project = project
        self.refresh()

    def refresh(self):
        """Refresh the tree from the project model."""
        self.clear()
        self._sprite_items.clear()
        self._scene_items.clear()

        if not self._project:
            return

        # Add project root
        root = QTreeWidgetItem(self, [self._project.name])
        root.setData(0, Qt.UserRole, ("project", self._project))
        root.setExpanded(True)

        # Add scenes
        for scene in self._project.scenes:
            scene_item = QTreeWidgetItem(root, [scene.name])
            scene_item.setData(0, Qt.UserRole, ("scene", scene))
            scene_item.setFlags(scene_item.flags() | Qt.ItemIsEditable)
            scene_item.setExpanded(True)
            self._scene_items[scene.id] = scene_item

            # Add sprites in scene
            for sprite in scene.sprites:
                sprite_item = QTreeWidgetItem(scene_item, [sprite.name])
                sprite_item.setData(0, Qt.UserRole, ("sprite", sprite))
                sprite_item.setFlags(sprite_item.flags() | Qt.ItemIsEditable)
                self._sprite_items[sprite.id] = sprite_item

    def select_sprite(self, sprite: SpriteModel):
        """Select a sprite in the tree."""
        if sprite.id in self._sprite_items:
            self.blockSignals(True)
            self.setCurrentItem(self._sprite_items[sprite.id])
            self.blockSignals(False)

    def _on_selection_changed(self):
        """Handle selection change."""
        items = self.selectedItems()
        if not items:
            return

        item = items[0]
        data = item.data(0, Qt.UserRole)

        if data:
            item_type, model = data
            if item_type == "sprite":
                self.sprite_selected.emit(model)
            elif item_type == "scene":
                self.scene_selected.emit(model)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click."""
        data = item.data(0, Qt.UserRole)
        if data:
            item_type, model = data
            if item_type == "sprite":
                self.sprite_double_clicked.emit(model)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle item rename."""
        data = item.data(0, Qt.UserRole)
        if data:
            item_type, model = data
            new_name = item.text(0)
            if model.name != new_name:
                model.name = new_name
                self.item_renamed.emit(model, new_name)

    def _show_context_menu(self, pos):
        """Show context menu."""
        item = self.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type, model = data
        menu = QMenu(self)

        if item_type == "project":
            add_scene_action = QAction(tr("hierarchy.add_scene"), self)
            add_scene_action.triggered.connect(self._add_scene)
            menu.addAction(add_scene_action)

        elif item_type == "scene":
            add_sprite_action = QAction(tr("hierarchy.add_sprite"), self)
            add_sprite_action.triggered.connect(lambda: self._add_sprite(model))
            menu.addAction(add_sprite_action)

            menu.addSeparator()

            rename_action = QAction(tr("hierarchy.rename"), self)
            rename_action.triggered.connect(lambda: self.editItem(item))
            menu.addAction(rename_action)

            delete_action = QAction(tr("hierarchy.delete_scene"), self)
            delete_action.triggered.connect(lambda: self._delete_scene(model))
            menu.addAction(delete_action)

        elif item_type == "sprite":
            rename_action = QAction(tr("hierarchy.rename"), self)
            rename_action.triggered.connect(lambda: self.editItem(item))
            menu.addAction(rename_action)

            duplicate_action = QAction(tr("hierarchy.duplicate"), self)
            duplicate_action.triggered.connect(lambda: self._duplicate_sprite(model))
            menu.addAction(duplicate_action)

            menu.addSeparator()

            delete_action = QAction(tr("hierarchy.delete_sprite"), self)
            delete_action.triggered.connect(lambda: self._delete_sprite(model))
            menu.addAction(delete_action)

        menu.exec_(self.mapToGlobal(pos))

    def _add_scene(self):
        """Add a new scene."""
        if not self._project:
            return

        name, ok = QInputDialog.getText(
            self, tr("dialog.add_scene_title"), tr("dialog.add_scene_prompt"),
            text=f"Scene{len(self._project.scenes) + 1}"
        )

        if ok and name:
            scene = SceneModel.create_default(name)
            self._project.add_scene(scene)
            self.refresh()

    def _add_sprite(self, scene: SceneModel):
        """Add a new sprite to a scene."""
        name, ok = QInputDialog.getText(
            self, tr("dialog.add_sprite_title"), tr("dialog.add_sprite_prompt"),
            text=f"Sprite{len(scene.sprites) + 1}"
        )

        if ok and name:
            sprite = SpriteModel.create_default(name)
            scene.add_sprite(sprite)
            self.refresh()

    def _delete_scene(self, scene: SceneModel):
        """Delete a scene."""
        if not self._project:
            return

        if len(self._project.scenes) <= 1:
            QMessageBox.warning(
                self, tr("hierarchy.cannot_delete"),
                tr("hierarchy.cannot_delete_last")
            )
            return

        reply = QMessageBox.question(
            self, tr("hierarchy.delete_scene"),
            tr("hierarchy.confirm_delete_scene").format(name=scene.name),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._project.remove_scene(scene.id)
            self.refresh()

    def _delete_sprite(self, sprite: SpriteModel):
        """Delete a sprite."""
        if not self._project:
            return

        reply = QMessageBox.question(
            self, tr("hierarchy.delete_sprite"),
            tr("hierarchy.confirm_delete_sprite").format(name=sprite.name),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for scene in self._project.scenes:
                if scene.remove_sprite(sprite.id):
                    break
            self.refresh()

    def _duplicate_sprite(self, sprite: SpriteModel):
        """Duplicate a sprite."""
        if not self._project:
            return

        # Find parent scene
        for scene in self._project.scenes:
            if sprite in scene.sprites:
                new_sprite = sprite.clone()
                new_sprite.x += 50
                new_sprite.y += 50
                scene.add_sprite(new_sprite)
                self.refresh()
                break
