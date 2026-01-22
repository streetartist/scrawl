"""
Property Editor

Inspector panel for editing sprite, scene, and game properties.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox,
    QSpinBox, QCheckBox, QLabel, QGroupBox, QScrollArea,
    QPushButton, QHBoxLayout, QColorDialog, QFileDialog,
    QListWidget, QListWidgetItem, QInputDialog, QMenu, QComboBox,
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette, QAction
from typing import Optional
import os

from models import SpriteModel, ProjectModel, GameSettings
from core.i18n import tr


class ColorButton(QPushButton):
    """A button that shows a color and opens a color dialog."""

    color_changed = Signal(tuple)

    def __init__(self, color=(255, 255, 255), parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._pick_color)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self._update_style()

    def _update_style(self):
        r, g, b = self._color
        self.setStyleSheet(
            f"background-color: rgb({r}, {g}, {b}); "
            f"border: 1px solid #555; min-width: 60px; min-height: 24px;"
        )

    def _pick_color(self):
        r, g, b = self._color
        color = QColorDialog.getColor(QColor(r, g, b), self, "Select Color")
        if color.isValid():
            self._color = (color.red(), color.green(), color.blue())
            self._update_style()
            self.color_changed.emit(self._color)


class PropertyEditor(QWidget):
    """Property editor for sprites and game settings."""

    property_changed = Signal(object, str, object)  # model, property_name, value
    game_property_changed = Signal(str, object)  # property_name, value

    def __init__(self, parent=None):
        super().__init__(parent)

        self._sprite: Optional[SpriteModel] = None
        self._game_settings: Optional[GameSettings] = None
        self._project: Optional[ProjectModel] = None
        self._updating = False

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Title
        self._title_label = QLabel(tr("inspector.no_selection"))
        self._title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        layout.addWidget(self._title_label)

        # Stacked widget for different property panels
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # Empty panel (index 0)
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.addStretch()
        self._stack.addWidget(empty_widget)

        # Sprite panel (index 1)
        self._sprite_panel = self._create_sprite_panel()
        self._stack.addWidget(self._sprite_panel)

        # Game settings panel (index 2)
        self._game_panel = self._create_game_panel()
        self._stack.addWidget(self._game_panel)

        # Initially show empty
        self._stack.setCurrentIndex(0)

    def _create_sprite_panel(self) -> QWidget:
        """Create the sprite properties panel."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignTop)

        # Identity group
        identity_group = QGroupBox(tr("inspector.identity"))
        identity_layout = QFormLayout(identity_group)

        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._on_name_changed)
        identity_layout.addRow(tr("inspector.name"), self._name_edit)

        self._class_edit = QLineEdit()
        self._class_edit.textChanged.connect(self._on_class_changed)
        identity_layout.addRow(tr("inspector.class"), self._class_edit)

        content_layout.addWidget(identity_group)

        # Transform group
        transform_group = QGroupBox(tr("inspector.transform"))
        transform_layout = QFormLayout(transform_group)

        # Position
        pos_widget = QWidget()
        pos_layout = QHBoxLayout(pos_widget)
        pos_layout.setContentsMargins(0, 0, 0, 0)

        self._x_spin = QDoubleSpinBox()
        self._x_spin.setRange(-10000, 10000)
        self._x_spin.setDecimals(1)
        self._x_spin.valueChanged.connect(self._on_x_changed)
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self._x_spin)

        self._y_spin = QDoubleSpinBox()
        self._y_spin.setRange(-10000, 10000)
        self._y_spin.setDecimals(1)
        self._y_spin.valueChanged.connect(self._on_y_changed)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self._y_spin)

        transform_layout.addRow(tr("inspector.position"), pos_widget)

        # Direction
        self._direction_spin = QDoubleSpinBox()
        self._direction_spin.setRange(-360, 360)
        self._direction_spin.setDecimals(1)
        self._direction_spin.setSuffix(" deg")
        self._direction_spin.valueChanged.connect(self._on_direction_changed)
        transform_layout.addRow(tr("inspector.direction"), self._direction_spin)

        # Size
        self._size_spin = QDoubleSpinBox()
        self._size_spin.setRange(0.01, 100)
        self._size_spin.setDecimals(2)
        self._size_spin.setSingleStep(0.1)
        self._size_spin.valueChanged.connect(self._on_size_changed)
        transform_layout.addRow(tr("inspector.size"), self._size_spin)

        content_layout.addWidget(transform_group)

        # Appearance group
        appearance_group = QGroupBox(tr("inspector.appearance"))
        appearance_layout = QFormLayout(appearance_group)

        self._visible_check = QCheckBox()
        self._visible_check.toggled.connect(self._on_visible_changed)
        appearance_layout.addRow(tr("inspector.visible"), self._visible_check)

        # Costumes list
        self._costumes_list = QListWidget()
        self._costumes_list.setMaximumHeight(100)
        self._costumes_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._costumes_list.customContextMenuRequested.connect(self._on_costume_context_menu)
        self._costumes_list.itemDoubleClicked.connect(self._on_costume_double_clicked)
        appearance_layout.addRow(tr("inspector.costumes"), self._costumes_list)

        # Default costume selector
        default_costume_widget = QWidget()
        default_costume_layout = QHBoxLayout(default_costume_widget)
        default_costume_layout.setContentsMargins(0, 0, 0, 0)
        self._default_costume_combo = QComboBox()
        self._default_costume_combo.currentIndexChanged.connect(self._on_default_costume_changed)
        default_costume_layout.addWidget(self._default_costume_combo)
        appearance_layout.addRow(tr("inspector.default_costume"), default_costume_widget)

        # Add costume button
        add_costume_btn = QPushButton(tr("inspector.add_costume"))
        add_costume_btn.clicked.connect(self._on_add_costume)
        appearance_layout.addRow("", add_costume_btn)

        content_layout.addWidget(appearance_group)

        # Spacer
        content_layout.addStretch()

        scroll.setWidget(content)
        return scroll

    def _create_game_panel(self) -> QWidget:
        """Create the game settings panel."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignTop)

        # Game info group
        info_group = QGroupBox(tr("inspector.game_info"))
        info_layout = QFormLayout(info_group)

        self._game_title_edit = QLineEdit()
        self._game_title_edit.textChanged.connect(self._on_game_title_changed)
        info_layout.addRow(tr("inspector.game_title"), self._game_title_edit)

        content_layout.addWidget(info_group)

        # Resolution group
        resolution_group = QGroupBox(tr("inspector.resolution"))
        resolution_layout = QFormLayout(resolution_group)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(320, 7680)
        self._width_spin.setSingleStep(10)
        self._width_spin.valueChanged.connect(self._on_width_changed)
        resolution_layout.addRow(tr("inspector.width"), self._width_spin)

        self._height_spin = QSpinBox()
        self._height_spin.setRange(240, 4320)
        self._height_spin.setSingleStep(10)
        self._height_spin.valueChanged.connect(self._on_height_changed)
        resolution_layout.addRow(tr("inspector.height"), self._height_spin)

        self._fullscreen_check = QCheckBox()
        self._fullscreen_check.toggled.connect(self._on_fullscreen_changed)
        resolution_layout.addRow(tr("inspector.fullscreen"), self._fullscreen_check)

        content_layout.addWidget(resolution_group)

        # Runtime group
        runtime_group = QGroupBox(tr("inspector.runtime"))
        runtime_layout = QFormLayout(runtime_group)

        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(1, 240)
        self._fps_spin.setSingleStep(1)
        self._fps_spin.valueChanged.connect(self._on_fps_changed)
        runtime_layout.addRow(tr("inspector.fps"), self._fps_spin)

        self._debug_check = QCheckBox()
        self._debug_check.toggled.connect(self._on_debug_changed)
        runtime_layout.addRow(tr("inspector.debug"), self._debug_check)

        content_layout.addWidget(runtime_group)

        # Spacer
        content_layout.addStretch()

        scroll.setWidget(content)
        return scroll

    def set_sprite(self, sprite: Optional[SpriteModel]):
        """Set the sprite to edit."""
        self._sprite = sprite
        self._game_settings = None

        if sprite is None:
            self._title_label.setText(tr("inspector.no_selection"))
            self._stack.setCurrentIndex(0)
            return

        self._stack.setCurrentIndex(1)
        self._refresh_sprite()

    def set_game_settings(self, project: ProjectModel):
        """Set the game settings to edit."""
        self._sprite = None
        self._project = project
        self._game_settings = project.game

        self._title_label.setText(tr("inspector.game_settings"))
        self._stack.setCurrentIndex(2)
        self._refresh_game_settings()

    def _refresh_sprite(self):
        """Refresh the sprite display."""
        if not self._sprite:
            return

        self._updating = True

        self._title_label.setText(self._sprite.name)
        self._name_edit.setText(self._sprite.name)
        self._class_edit.setText(self._sprite.class_name)
        self._x_spin.setValue(self._sprite.x)
        self._y_spin.setValue(self._sprite.y)
        self._direction_spin.setValue(self._sprite.direction)
        self._size_spin.setValue(self._sprite.size)
        self._visible_check.setChecked(self._sprite.visible)

        # Costumes
        self._costumes_list.clear()
        self._default_costume_combo.clear()
        for i, costume in enumerate(self._sprite.costumes):
            item = QListWidgetItem(costume.name)
            item.setToolTip(costume.path)
            item.setData(Qt.UserRole, i)
            self._costumes_list.addItem(item)
            self._default_costume_combo.addItem(costume.name)

        if self._sprite.costumes:
            self._default_costume_combo.setCurrentIndex(self._sprite.default_costume)

        self._updating = False

    def _refresh_game_settings(self):
        """Refresh the game settings display."""
        if not self._game_settings:
            return

        self._updating = True

        self._game_title_edit.setText(self._game_settings.title)
        self._width_spin.setValue(self._game_settings.width)
        self._height_spin.setValue(self._game_settings.height)
        self._fullscreen_check.setChecked(self._game_settings.fullscreen)
        self._fps_spin.setValue(self._game_settings.fps)
        self._debug_check.setChecked(self._game_settings.debug)

        self._updating = False

    def refresh(self):
        """Refresh the current display."""
        if self._sprite:
            self._refresh_sprite()
        elif self._game_settings:
            self._refresh_game_settings()

    # Sprite property change handlers
    def _on_name_changed(self, text: str):
        if self._updating or not self._sprite:
            return
        self._sprite.name = text
        self._title_label.setText(text)
        self.property_changed.emit(self._sprite, "name", text)

    def _on_class_changed(self, text: str):
        if self._updating or not self._sprite:
            return
        self._sprite.class_name = text
        self.property_changed.emit(self._sprite, "class_name", text)

    def _on_x_changed(self, value: float):
        if self._updating or not self._sprite:
            return
        self._sprite.x = value
        self.property_changed.emit(self._sprite, "x", value)

    def _on_y_changed(self, value: float):
        if self._updating or not self._sprite:
            return
        self._sprite.y = value
        self.property_changed.emit(self._sprite, "y", value)

    def _on_direction_changed(self, value: float):
        if self._updating or not self._sprite:
            return
        self._sprite.direction = value
        self.property_changed.emit(self._sprite, "direction", value)

    def _on_size_changed(self, value: float):
        if self._updating or not self._sprite:
            return
        self._sprite.size = value
        self.property_changed.emit(self._sprite, "size", value)

    def _on_visible_changed(self, checked: bool):
        if self._updating or not self._sprite:
            return
        self._sprite.visible = checked
        self.property_changed.emit(self._sprite, "visible", checked)

    def _on_add_costume(self):
        if not self._sprite:
            return

        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.select_costume"), "",
            tr("dialog.image_filter")
        )

        if path:
            default_name = os.path.splitext(os.path.basename(path))[0]
            name, ok = QInputDialog.getText(
                self, tr("inspector.costume_name"), tr("inspector.costume_name_prompt"),
                text=default_name
            )
            if not ok or not name:
                name = default_name

            idx = self._sprite.add_costume(name, path)
            if len(self._sprite.costumes) == 1:
                self._sprite.current_costume = 0
                self._sprite.default_costume = 0
            self._refresh_sprite()
            self.property_changed.emit(self._sprite, "costumes", self._sprite.costumes)

    def _on_default_costume_changed(self, index: int):
        if self._updating or not self._sprite or index < 0:
            return
        self._sprite.default_costume = index
        self.property_changed.emit(self._sprite, "default_costume", index)

    def _on_costume_context_menu(self, pos):
        if not self._sprite:
            return

        item = self._costumes_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        rename_action = QAction(tr("inspector.rename_costume"), self)
        rename_action.triggered.connect(lambda: self._rename_costume(item))
        menu.addAction(rename_action)

        set_default_action = QAction(tr("inspector.set_as_default"), self)
        set_default_action.triggered.connect(lambda: self._set_costume_as_default(item))
        menu.addAction(set_default_action)

        delete_action = QAction(tr("inspector.delete_costume"), self)
        delete_action.triggered.connect(lambda: self._delete_costume(item))
        menu.addAction(delete_action)

        menu.exec_(self._costumes_list.mapToGlobal(pos))

    def _on_costume_double_clicked(self, item):
        if not self._sprite:
            return
        index = item.data(Qt.UserRole)
        if index is not None:
            self._sprite.current_costume = index
            self.property_changed.emit(self._sprite, "current_costume", index)

    def _rename_costume(self, item):
        if not self._sprite:
            return
        index = item.data(Qt.UserRole)
        if index is None or index >= len(self._sprite.costumes):
            return

        costume = self._sprite.costumes[index]
        new_name, ok = QInputDialog.getText(
            self, tr("inspector.rename_costume"), tr("inspector.rename_costume_prompt"),
            text=costume.name
        )
        if ok and new_name:
            costume.name = new_name
            self._refresh_sprite()
            self.property_changed.emit(self._sprite, "costumes", self._sprite.costumes)

    def _set_costume_as_default(self, item):
        if not self._sprite:
            return
        index = item.data(Qt.UserRole)
        if index is not None:
            self._sprite.default_costume = index
            self._default_costume_combo.setCurrentIndex(index)
            self.property_changed.emit(self._sprite, "default_costume", index)

    def _delete_costume(self, item):
        if not self._sprite:
            return
        index = item.data(Qt.UserRole)
        if index is not None and index < len(self._sprite.costumes):
            del self._sprite.costumes[index]
            if self._sprite.current_costume >= len(self._sprite.costumes):
                self._sprite.current_costume = max(0, len(self._sprite.costumes) - 1)
            if self._sprite.default_costume >= len(self._sprite.costumes):
                self._sprite.default_costume = max(0, len(self._sprite.costumes) - 1)
            self._refresh_sprite()
            self.property_changed.emit(self._sprite, "costumes", self._sprite.costumes)

    # Game settings property change handlers
    def _on_game_title_changed(self, text: str):
        if self._updating or not self._game_settings:
            return
        self._game_settings.title = text
        self.game_property_changed.emit("title", text)

    def _on_width_changed(self, value: int):
        if self._updating or not self._game_settings:
            return
        self._game_settings.width = value
        self.game_property_changed.emit("width", value)

    def _on_height_changed(self, value: int):
        if self._updating or not self._game_settings:
            return
        self._game_settings.height = value
        self.game_property_changed.emit("height", value)

    def _on_fullscreen_changed(self, checked: bool):
        if self._updating or not self._game_settings:
            return
        self._game_settings.fullscreen = checked
        self.game_property_changed.emit("fullscreen", checked)

    def _on_fps_changed(self, value: int):
        if self._updating or not self._game_settings:
            return
        self._game_settings.fps = value
        self.game_property_changed.emit("fps", value)

    def _on_debug_changed(self, checked: bool):
        if self._updating or not self._game_settings:
            return
        self._game_settings.debug = checked
        self.game_property_changed.emit("debug", checked)
