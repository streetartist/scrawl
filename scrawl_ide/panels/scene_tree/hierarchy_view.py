"""
Hierarchy View

Tree view showing the scene hierarchy (scenes and sprites).
"""

from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QMenu, QInputDialog, QMessageBox, QDialog, QListWidget,
    QListWidgetItem, QDialogButtonBox, QLabel, QHBoxLayout, QTabWidget,
    QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont
from typing import Optional, Dict

from models import ProjectModel, SceneModel, SpriteModel
from models.sprite_model import NODE_CATEGORIES, NODE_ICONS
from core.i18n import tr


class AddNodeDialog(QDialog):
    """Dialog for selecting a node type to add."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加节点")
        self.setMinimumSize(420, 500)
        self.selected_type = None

        layout = QVBoxLayout(self)

        # Search box
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索节点类型...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Tree view with categories as parent items, node types as children
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(20)
        self._tree.setAnimated(True)

        category_font = QFont()
        category_font.setBold(True)

        self._category_items: Dict[str, QTreeWidgetItem] = {}
        self._node_items: list = []

        for category, types in NODE_CATEGORIES.items():
            cat_item = QTreeWidgetItem(self._tree, [f"📁 {category}"])
            cat_item.setFont(0, category_font)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
            cat_item.setExpanded(True)
            self._category_items[category] = cat_item

            for t in types:
                icon = NODE_ICONS.get(t, "")
                node_item = QTreeWidgetItem(cat_item, [f"{icon}  {t}"])
                node_item.setData(0, Qt.UserRole, t)
                self._node_items.append(node_item)

        self._tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._tree)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_search(self, text: str):
        text = text.strip().lower()
        for cat_item in self._category_items.values():
            any_visible = False
            for i in range(cat_item.childCount()):
                child = cat_item.child(i)
                node_type = child.data(0, Qt.UserRole) or ""
                visible = not text or text in node_type.lower()
                child.setHidden(not visible)
                if visible:
                    any_visible = True
            cat_item.setHidden(not any_visible)
            if any_visible:
                cat_item.setExpanded(True)

    def _on_accept(self):
        current = self._tree.currentItem()
        if current and current.data(0, Qt.UserRole):
            self.selected_type = current.data(0, Qt.UserRole)
            self.accept()

    def _on_double_click(self, item):
        node_type = item.data(0, Qt.UserRole)
        if node_type:
            self.selected_type = node_type
            self.accept()


class HierarchyView(QTreeWidget):
    """Tree view showing project hierarchy."""

    sprite_selected = Signal(object)  # SpriteModel
    sprite_double_clicked = Signal(object)  # SpriteModel
    scene_selected = Signal(object)  # SceneModel
    scene_double_clicked = Signal(object)  # SceneModel
    project_selected = Signal()  # Project root selected
    item_renamed = Signal(object, str)  # model, new_name
    sprite_added = Signal(object, object)  # SceneModel, SpriteModel
    sprite_removed = Signal(object, object)  # SceneModel, SpriteModel
    scene_added = Signal(object)  # SceneModel
    scene_removed = Signal(object)  # SceneModel

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
                icon = NODE_ICONS.get(sprite.node_type, "🔷")
                sprite_item = QTreeWidgetItem(scene_item, [f"{icon} {sprite.name}"])
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
            elif item_type == "project":
                self.project_selected.emit()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click."""
        data = item.data(0, Qt.UserRole)
        if data:
            item_type, model = data
            if item_type == "sprite":
                self.sprite_double_clicked.emit(model)
            elif item_type == "scene":
                self.scene_double_clicked.emit(model)

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
            add_node_action = QAction("添加节点...", self)
            add_node_action.triggered.connect(lambda: self._add_node(model))
            menu.addAction(add_node_action)

            # Quick-add submenu for common types
            quick_menu = QMenu("快速添加", self)
            for node_type in ["Sprite", "PhysicsSprite", "Camera2D", "Label", "Timer"]:
                icon = NODE_ICONS.get(node_type, "")
                act = QAction(f"{icon} {node_type}", self)
                act.triggered.connect(lambda checked, nt=node_type: self._add_sprite(model, nt))
                quick_menu.addAction(act)
            menu.addMenu(quick_menu)

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
            self.scene_added.emit(scene)

    def _add_node(self, scene: SceneModel):
        """Add a new node to a scene via type selection dialog."""
        dialog = AddNodeDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_type:
            node_type = dialog.selected_type
            name, ok = QInputDialog.getText(
                self, "添加节点", "节点名称:",
                text=f"{node_type}{len(scene.sprites) + 1}"
            )
            if ok and name:
                sprite = SpriteModel.create_default(name, node_type)
                scene.add_sprite(sprite)
                self.refresh()
                self.sprite_added.emit(scene, sprite)

    def _add_sprite(self, scene: SceneModel, node_type: str = "Sprite"):
        """Add a new sprite to a scene."""
        name, ok = QInputDialog.getText(
            self, tr("dialog.add_sprite_title"), tr("dialog.add_sprite_prompt"),
            text=f"{node_type}{len(scene.sprites) + 1}"
        )

        if ok and name:
            sprite = SpriteModel.create_default(name, node_type)
            scene.add_sprite(sprite)
            self.refresh()
            self.sprite_added.emit(scene, sprite)

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
            self.scene_removed.emit(scene)

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
                    self.refresh()
                    self.sprite_removed.emit(scene, sprite)
                    break

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
                self.sprite_added.emit(scene, new_sprite)
                break
