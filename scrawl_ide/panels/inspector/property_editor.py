"""
Property Editor

Inspector panel for editing sprite and scene properties.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox,
    QSpinBox, QCheckBox, QLabel, QGroupBox, QScrollArea,
    QPushButton, QHBoxLayout, QColorDialog, QFileDialog,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from typing import Optional

from models import SpriteModel
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
    """Property editor for sprites and other objects."""

    property_changed = Signal(object, str, object)  # model, property_name, value

    def __init__(self, parent=None):
        super().__init__(parent)

        self._sprite: Optional[SpriteModel] = None
        self._updating = False

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setAlignment(Qt.AlignTop)

        # Title
        self._title_label = QLabel(tr("inspector.no_selection"))
        self._title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        self._content_layout.addWidget(self._title_label)

        # Identity group
        identity_group = QGroupBox(tr("inspector.identity"))
        identity_layout = QFormLayout(identity_group)

        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._on_name_changed)
        identity_layout.addRow(tr("inspector.name"), self._name_edit)

        self._class_edit = QLineEdit()
        self._class_edit.textChanged.connect(self._on_class_changed)
        identity_layout.addRow(tr("inspector.class"), self._class_edit)

        self._content_layout.addWidget(identity_group)

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

        self._content_layout.addWidget(transform_group)

        # Appearance group
        appearance_group = QGroupBox(tr("inspector.appearance"))
        appearance_layout = QFormLayout(appearance_group)

        self._visible_check = QCheckBox()
        self._visible_check.toggled.connect(self._on_visible_changed)
        appearance_layout.addRow(tr("inspector.visible"), self._visible_check)

        # Costumes list
        self._costumes_list = QListWidget()
        self._costumes_list.setMaximumHeight(100)
        appearance_layout.addRow(tr("inspector.costumes"), self._costumes_list)

        # Add costume button
        add_costume_btn = QPushButton(tr("inspector.add_costume"))
        add_costume_btn.clicked.connect(self._on_add_costume)
        appearance_layout.addRow("", add_costume_btn)

        self._content_layout.addWidget(appearance_group)

        # Script group
        script_group = QGroupBox(tr("inspector.script"))
        script_layout = QFormLayout(script_group)

        script_widget = QWidget()
        script_h_layout = QHBoxLayout(script_widget)
        script_h_layout.setContentsMargins(0, 0, 0, 0)

        self._script_edit = QLineEdit()
        self._script_edit.setReadOnly(True)
        script_h_layout.addWidget(self._script_edit)

        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(30)
        browse_btn.clicked.connect(self._on_browse_script)
        script_h_layout.addWidget(browse_btn)

        script_layout.addRow(tr("inspector.script_path"), script_widget)

        self._content_layout.addWidget(script_group)

        # Spacer
        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Initially disabled
        self._set_enabled(False)

    def _set_enabled(self, enabled: bool):
        """Enable or disable all controls."""
        self._name_edit.setEnabled(enabled)
        self._class_edit.setEnabled(enabled)
        self._x_spin.setEnabled(enabled)
        self._y_spin.setEnabled(enabled)
        self._direction_spin.setEnabled(enabled)
        self._size_spin.setEnabled(enabled)
        self._visible_check.setEnabled(enabled)
        self._costumes_list.setEnabled(enabled)
        self._script_edit.setEnabled(enabled)

    def set_sprite(self, sprite: Optional[SpriteModel]):
        """Set the sprite to edit."""
        self._sprite = sprite

        if sprite is None:
            self._title_label.setText(tr("inspector.no_selection"))
            self._set_enabled(False)
            return

        self._set_enabled(True)
        self.refresh()

    def refresh(self):
        """Refresh the display from the current sprite."""
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
        for costume in self._sprite.costumes:
            self._costumes_list.addItem(costume)

        # Script
        self._script_edit.setText(self._sprite.script_path or "")

        self._updating = False

    # Property change handlers
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
            self._sprite.costumes.append(path)
            self._costumes_list.addItem(path)
            self.property_changed.emit(self._sprite, "costumes", self._sprite.costumes)

    def _on_browse_script(self):
        if not self._sprite:
            return

        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.select_script"), "",
            tr("dialog.python_filter")
        )

        if path:
            self._sprite.script_path = path
            self._script_edit.setText(path)
            self.property_changed.emit(self._sprite, "script_path", path)
