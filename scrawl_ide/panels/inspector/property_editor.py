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

from models import SpriteModel, ProjectModel, GameSettings, SceneModel
from models.sprite_model import NODE_CATEGORIES, NODE_ICONS, VISUAL_NODE_TYPES, PHYSICS_NODE_TYPES
from core.i18n import tr
from .code_costume_dialog import CodeCostumeDialog
from .tilemap_editor import TileMapEditor
from .spriteframes_editor import SpriteFramesEditor
from .path_editor import PathEditor
from .navigation_editor import NavigationGridEditor


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
    scene_property_changed = Signal(object, str, object)  # scene, property_name, value

    def __init__(self, parent=None):
        super().__init__(parent)

        self._sprite: Optional[SpriteModel] = None
        self._scene: Optional[SceneModel] = None
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

        # Scene panel (index 2)
        self._scene_panel = self._create_scene_panel()
        self._stack.addWidget(self._scene_panel)

        # Game settings panel (index 3)
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

        # Node type selector
        self._node_type_combo = QComboBox()
        all_types = []
        for types in NODE_CATEGORIES.values():
            all_types.extend(types)
        self._node_type_combo.addItems(all_types)
        self._node_type_combo.currentTextChanged.connect(self._on_node_type_changed)
        identity_layout.addRow("节点类型:", self._node_type_combo)

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

        # Add code costume button
        add_code_costume_btn = QPushButton("代码绘制造型...")
        add_code_costume_btn.clicked.connect(self._on_add_code_costume)
        appearance_layout.addRow("", add_code_costume_btn)

        content_layout.addWidget(appearance_group)

        # Collision group
        collision_group = QGroupBox(tr("inspector.collision"))
        collision_layout = QFormLayout(collision_group)

        self._collision_type_combo = QComboBox()
        self._collision_type_combo.addItems(["rect", "circle", "mask"])
        self._collision_type_combo.currentTextChanged.connect(self._on_collision_type_changed)
        collision_layout.addRow(tr("inspector.collision_type"), self._collision_type_combo)

        content_layout.addWidget(collision_group)

        # Physics group
        physics_group = QGroupBox(tr("inspector.physics"))
        physics_layout = QFormLayout(physics_group)

        self._is_physics_check = QCheckBox()
        self._is_physics_check.toggled.connect(self._on_is_physics_changed)
        physics_layout.addRow(tr("inspector.is_physics"), self._is_physics_check)

        # Gravity
        gravity_widget = QWidget()
        gravity_layout = QHBoxLayout(gravity_widget)
        gravity_layout.setContentsMargins(0, 0, 0, 0)

        self._gravity_x_spin = QDoubleSpinBox()
        self._gravity_x_spin.setRange(-10, 10)
        self._gravity_x_spin.setDecimals(2)
        self._gravity_x_spin.setSingleStep(0.1)
        self._gravity_x_spin.valueChanged.connect(self._on_gravity_x_changed)
        gravity_layout.addWidget(QLabel("X:"))
        gravity_layout.addWidget(self._gravity_x_spin)

        self._gravity_y_spin = QDoubleSpinBox()
        self._gravity_y_spin.setRange(-10, 10)
        self._gravity_y_spin.setDecimals(2)
        self._gravity_y_spin.setSingleStep(0.1)
        self._gravity_y_spin.valueChanged.connect(self._on_gravity_y_changed)
        gravity_layout.addWidget(QLabel("Y:"))
        gravity_layout.addWidget(self._gravity_y_spin)

        physics_layout.addRow(tr("inspector.gravity"), gravity_widget)

        # Friction
        self._friction_spin = QDoubleSpinBox()
        self._friction_spin.setRange(0, 1)
        self._friction_spin.setDecimals(2)
        self._friction_spin.setSingleStep(0.01)
        self._friction_spin.valueChanged.connect(self._on_friction_changed)
        physics_layout.addRow(tr("inspector.friction"), self._friction_spin)

        # Elasticity
        self._elasticity_spin = QDoubleSpinBox()
        self._elasticity_spin.setRange(0, 1)
        self._elasticity_spin.setDecimals(2)
        self._elasticity_spin.setSingleStep(0.1)
        self._elasticity_spin.valueChanged.connect(self._on_elasticity_changed)
        physics_layout.addRow(tr("inspector.elasticity"), self._elasticity_spin)

        content_layout.addWidget(physics_group)

        # --- Camera2D group ---
        self._camera_group = QGroupBox("📷 Camera2D")
        camera_layout = QFormLayout(self._camera_group)

        self._camera_zoom_spin = QDoubleSpinBox()
        self._camera_zoom_spin.setRange(0.1, 10.0)
        self._camera_zoom_spin.setDecimals(2)
        self._camera_zoom_spin.setSingleStep(0.1)
        self._camera_zoom_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("camera_zoom", v))
        camera_layout.addRow("缩放:", self._camera_zoom_spin)

        self._camera_smoothing_check = QCheckBox()
        self._camera_smoothing_check.toggled.connect(lambda v: self._on_typed_prop_changed("camera_smoothing", v))
        camera_layout.addRow("平滑:", self._camera_smoothing_check)

        self._camera_smoothing_speed_spin = QDoubleSpinBox()
        self._camera_smoothing_speed_spin.setRange(0.1, 50.0)
        self._camera_smoothing_speed_spin.setDecimals(1)
        self._camera_smoothing_speed_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("camera_smoothing_speed", v))
        camera_layout.addRow("平滑速度:", self._camera_smoothing_speed_spin)

        self._camera_follow_edit = QLineEdit()
        self._camera_follow_edit.setPlaceholderText("目标节点名称")
        self._camera_follow_edit.textChanged.connect(lambda v: self._on_typed_prop_changed("camera_follow_target", v))
        camera_layout.addRow("跟随目标:", self._camera_follow_edit)

        self._camera_group.setVisible(False)
        content_layout.addWidget(self._camera_group)

        # --- Light2D group ---
        self._light_group = QGroupBox("💡 Light2D")
        light_layout = QFormLayout(self._light_group)

        self._light_color_btn = ColorButton((255, 255, 255))
        self._light_color_btn.color_changed.connect(lambda v: self._on_typed_prop_changed("light_color", v))
        light_layout.addRow("颜色:", self._light_color_btn)

        self._light_energy_spin = QDoubleSpinBox()
        self._light_energy_spin.setRange(0.0, 10.0)
        self._light_energy_spin.setDecimals(2)
        self._light_energy_spin.setSingleStep(0.1)
        self._light_energy_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("light_energy", v))
        light_layout.addRow("强度:", self._light_energy_spin)

        self._light_radius_spin = QDoubleSpinBox()
        self._light_radius_spin.setRange(1.0, 2000.0)
        self._light_radius_spin.setDecimals(0)
        self._light_radius_spin.setSingleStep(10)
        self._light_radius_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("light_radius", v))
        light_layout.addRow("半径:", self._light_radius_spin)

        self._light_shadow_check = QCheckBox()
        self._light_shadow_check.toggled.connect(lambda v: self._on_typed_prop_changed("light_shadow", v))
        light_layout.addRow("阴影:", self._light_shadow_check)

        self._light_group.setVisible(False)
        content_layout.addWidget(self._light_group)

        # --- AudioPlayer2D group ---
        self._audio_group = QGroupBox("🔊 AudioPlayer2D")
        audio_layout = QFormLayout(self._audio_group)

        audio_stream_w = QWidget()
        audio_stream_l = QHBoxLayout(audio_stream_w)
        audio_stream_l.setContentsMargins(0, 0, 0, 0)
        self._audio_stream_edit = QLineEdit()
        self._audio_stream_edit.setReadOnly(True)
        self._audio_stream_edit.setPlaceholderText("选择音频文件...")
        audio_stream_l.addWidget(self._audio_stream_edit)
        audio_browse_btn = QPushButton("...")
        audio_browse_btn.setFixedWidth(40)
        audio_browse_btn.clicked.connect(self._on_browse_audio)
        audio_stream_l.addWidget(audio_browse_btn)
        audio_layout.addRow("音频文件:", audio_stream_w)

        self._audio_volume_spin = QDoubleSpinBox()
        self._audio_volume_spin.setRange(0.0, 2.0)
        self._audio_volume_spin.setDecimals(2)
        self._audio_volume_spin.setSingleStep(0.1)
        self._audio_volume_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("audio_volume", v))
        audio_layout.addRow("音量:", self._audio_volume_spin)

        self._audio_pitch_spin = QDoubleSpinBox()
        self._audio_pitch_spin.setRange(0.1, 4.0)
        self._audio_pitch_spin.setDecimals(2)
        self._audio_pitch_spin.setSingleStep(0.1)
        self._audio_pitch_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("audio_pitch", v))
        audio_layout.addRow("音调:", self._audio_pitch_spin)

        self._audio_autoplay_check = QCheckBox()
        self._audio_autoplay_check.toggled.connect(lambda v: self._on_typed_prop_changed("audio_autoplay", v))
        audio_layout.addRow("自动播放:", self._audio_autoplay_check)

        self._audio_loop_check = QCheckBox()
        self._audio_loop_check.toggled.connect(lambda v: self._on_typed_prop_changed("audio_loop", v))
        audio_layout.addRow("循环:", self._audio_loop_check)

        self._audio_group.setVisible(False)
        content_layout.addWidget(self._audio_group)

        # --- ParticleEmitter2D group ---
        self._particle_group = QGroupBox("✨ ParticleEmitter2D")
        particle_layout = QFormLayout(self._particle_group)

        self._particle_amount_spin = QSpinBox()
        self._particle_amount_spin.setRange(1, 1000)
        self._particle_amount_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("particle_amount", v))
        particle_layout.addRow("粒子数:", self._particle_amount_spin)

        self._particle_lifetime_spin = QDoubleSpinBox()
        self._particle_lifetime_spin.setRange(0.1, 30.0)
        self._particle_lifetime_spin.setDecimals(1)
        self._particle_lifetime_spin.setSingleStep(0.5)
        self._particle_lifetime_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("particle_lifetime", v))
        particle_layout.addRow("生命周期:", self._particle_lifetime_spin)

        self._particle_emitting_check = QCheckBox()
        self._particle_emitting_check.toggled.connect(lambda v: self._on_typed_prop_changed("particle_emitting", v))
        particle_layout.addRow("发射中:", self._particle_emitting_check)

        self._particle_preset_combo = QComboBox()
        self._particle_preset_combo.addItems(["", "fire", "smoke", "sparkle", "rain", "snow", "explosion"])
        self._particle_preset_combo.currentTextChanged.connect(lambda v: self._on_typed_prop_changed("particle_preset", v))
        particle_layout.addRow("预设:", self._particle_preset_combo)

        self._particle_group.setVisible(False)
        content_layout.addWidget(self._particle_group)

        # --- UI group (Label, Button, ProgressBar, Panel) ---
        self._ui_group = QGroupBox("🏷️ UI")
        ui_layout = QFormLayout(self._ui_group)

        self._ui_text_edit = QLineEdit()
        self._ui_text_edit.textChanged.connect(lambda v: self._on_typed_prop_changed("ui_text", v))
        ui_layout.addRow("文本:", self._ui_text_edit)

        self._ui_font_size_spin = QSpinBox()
        self._ui_font_size_spin.setRange(6, 200)
        self._ui_font_size_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("ui_font_size", v))
        ui_layout.addRow("字号:", self._ui_font_size_spin)

        self._ui_text_color_btn = ColorButton((255, 255, 255))
        self._ui_text_color_btn.color_changed.connect(lambda v: self._on_typed_prop_changed("ui_text_color", v))
        ui_layout.addRow("文字颜色:", self._ui_text_color_btn)

        self._ui_min_spin = QDoubleSpinBox()
        self._ui_min_spin.setRange(-99999, 99999)
        self._ui_min_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("ui_min_value", v))
        ui_layout.addRow("最小值:", self._ui_min_spin)

        self._ui_max_spin = QDoubleSpinBox()
        self._ui_max_spin.setRange(-99999, 99999)
        self._ui_max_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("ui_max_value", v))
        ui_layout.addRow("最大值:", self._ui_max_spin)

        self._ui_value_spin = QDoubleSpinBox()
        self._ui_value_spin.setRange(-99999, 99999)
        self._ui_value_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("ui_value", v))
        ui_layout.addRow("当前值:", self._ui_value_spin)

        self._ui_group.setVisible(False)
        content_layout.addWidget(self._ui_group)

        # --- Timer group ---
        self._timer_group = QGroupBox("⏱️ Timer")
        timer_layout = QFormLayout(self._timer_group)

        self._timer_wait_spin = QDoubleSpinBox()
        self._timer_wait_spin.setRange(0.01, 3600.0)
        self._timer_wait_spin.setDecimals(2)
        self._timer_wait_spin.setSingleStep(0.1)
        self._timer_wait_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("timer_wait_time", v))
        timer_layout.addRow("等待时间(秒):", self._timer_wait_spin)

        self._timer_oneshot_check = QCheckBox()
        self._timer_oneshot_check.toggled.connect(lambda v: self._on_typed_prop_changed("timer_one_shot", v))
        timer_layout.addRow("一次性:", self._timer_oneshot_check)

        self._timer_autostart_check = QCheckBox()
        self._timer_autostart_check.toggled.connect(lambda v: self._on_typed_prop_changed("timer_autostart", v))
        timer_layout.addRow("自动开始:", self._timer_autostart_check)

        self._timer_group.setVisible(False)
        content_layout.addWidget(self._timer_group)

        # --- TileMap group ---
        self._tilemap_group = QGroupBox("🗺️ TileMap")
        tilemap_layout = QFormLayout(self._tilemap_group)

        self._tilemap_cellsize_spin = QSpinBox()
        self._tilemap_cellsize_spin.setRange(4, 256)
        self._tilemap_cellsize_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("tilemap_cell_size", v))
        tilemap_layout.addRow("单元格大小:", self._tilemap_cellsize_spin)

        self._tilemap_group.setVisible(False)
        content_layout.addWidget(self._tilemap_group)

        # --- Collision Shape group ---
        self._collision_shape_group = QGroupBox("碰撞形状")
        cs_layout = QFormLayout(self._collision_shape_group)

        self._collision_shape_combo = QComboBox()
        self._collision_shape_combo.addItems(["rectangle", "circle", "capsule"])
        self._collision_shape_combo.currentTextChanged.connect(lambda v: self._on_typed_prop_changed("collision_shape", v))
        cs_layout.addRow("形状:", self._collision_shape_combo)

        self._collision_width_spin = QDoubleSpinBox()
        self._collision_width_spin.setRange(1, 2000)
        self._collision_width_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("collision_width", v))
        cs_layout.addRow("宽度:", self._collision_width_spin)

        self._collision_height_spin = QDoubleSpinBox()
        self._collision_height_spin.setRange(1, 2000)
        self._collision_height_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("collision_height", v))
        cs_layout.addRow("高度:", self._collision_height_spin)

        self._collision_radius_spin = QDoubleSpinBox()
        self._collision_radius_spin.setRange(1, 2000)
        self._collision_radius_spin.valueChanged.connect(lambda v: self._on_typed_prop_changed("collision_radius", v))
        cs_layout.addRow("半径:", self._collision_radius_spin)

        self._collision_shape_group.setVisible(False)
        content_layout.addWidget(self._collision_shape_group)

        # --- TileMap Editor ---
        self._tilemap_editor_group = QGroupBox("🗺️ 瓦片地图编辑器")
        tme_layout = QVBoxLayout(self._tilemap_editor_group)
        self._tilemap_editor = TileMapEditor()
        self._tilemap_editor.data_changed.connect(self._on_tilemap_data_changed)
        tme_layout.addWidget(self._tilemap_editor)
        self._tilemap_editor_group.setVisible(False)
        content_layout.addWidget(self._tilemap_editor_group)

        # --- SpriteFrames Editor ---
        self._spriteframes_editor_group = QGroupBox("🎞️ 帧动画编辑器")
        sfe_layout = QVBoxLayout(self._spriteframes_editor_group)
        self._spriteframes_editor = SpriteFramesEditor()
        self._spriteframes_editor.data_changed.connect(self._on_spriteframes_data_changed)
        sfe_layout.addWidget(self._spriteframes_editor)
        self._spriteframes_editor_group.setVisible(False)
        content_layout.addWidget(self._spriteframes_editor_group)

        # --- Path Editor ---
        self._path_editor_group = QGroupBox("📐 路径编辑器")
        pe_layout = QVBoxLayout(self._path_editor_group)
        self._path_editor = PathEditor()
        self._path_editor.data_changed.connect(self._on_path_data_changed)
        pe_layout.addWidget(self._path_editor)
        self._path_editor_group.setVisible(False)
        content_layout.addWidget(self._path_editor_group)

        # --- Navigation Grid Editor ---
        self._nav_editor_group = QGroupBox("🧭 导航网格编辑器")
        ne_layout = QVBoxLayout(self._nav_editor_group)
        self._nav_editor = NavigationGridEditor()
        self._nav_editor.data_changed.connect(self._on_nav_data_changed)
        ne_layout.addWidget(self._nav_editor)
        self._nav_editor_group.setVisible(False)
        content_layout.addWidget(self._nav_editor_group)

        # Spacer
        content_layout.addStretch()

        scroll.setWidget(content)
        return scroll

    def _create_scene_panel(self) -> QWidget:
        """Create the scene properties panel."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignTop)

        # Identity group
        identity_group = QGroupBox(tr("inspector.identity"))
        identity_layout = QFormLayout(identity_group)

        self._scene_name_edit = QLineEdit()
        self._scene_name_edit.textChanged.connect(self._on_scene_name_changed)
        identity_layout.addRow(tr("inspector.name"), self._scene_name_edit)

        content_layout.addWidget(identity_group)

        # Background group
        background_group = QGroupBox(tr("inspector.background"))
        background_layout = QFormLayout(background_group)

        # Background color
        self._bg_color_btn = ColorButton()
        self._bg_color_btn.color_changed.connect(self._on_bg_color_changed)
        background_layout.addRow(tr("inspector.bg_color"), self._bg_color_btn)

        # Background image
        bg_image_widget = QWidget()
        bg_image_layout = QHBoxLayout(bg_image_widget)
        bg_image_layout.setContentsMargins(0, 0, 0, 0)

        self._bg_image_edit = QLineEdit()
        self._bg_image_edit.setReadOnly(True)
        self._bg_image_edit.setPlaceholderText(tr("inspector.no_bg_image"))
        bg_image_layout.addWidget(self._bg_image_edit)

        browse_bg_btn = QPushButton("...")
        browse_bg_btn.setFixedWidth(40)
        browse_bg_btn.setStyleSheet("padding: 4px 8px;")
        browse_bg_btn.clicked.connect(self._on_browse_bg_image)
        bg_image_layout.addWidget(browse_bg_btn)

        clear_bg_btn = QPushButton("X")
        clear_bg_btn.setFixedWidth(40)
        clear_bg_btn.setStyleSheet("padding: 4px 8px;")
        clear_bg_btn.clicked.connect(self._on_clear_bg_image)
        bg_image_layout.addWidget(clear_bg_btn)

        background_layout.addRow(tr("inspector.bg_image"), bg_image_widget)

        content_layout.addWidget(background_group)

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

        # Sounds group
        sounds_group = QGroupBox(tr("inspector.sounds"))
        sounds_layout = QVBoxLayout(sounds_group)

        # Sounds list
        self._sounds_list = QListWidget()
        self._sounds_list.setMaximumHeight(120)
        self._sounds_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._sounds_list.customContextMenuRequested.connect(self._on_sound_context_menu)
        sounds_layout.addWidget(self._sounds_list)

        # Add sound button
        add_sound_btn = QPushButton(tr("inspector.add_sound"))
        add_sound_btn.clicked.connect(self._on_add_sound)
        sounds_layout.addWidget(add_sound_btn)

        content_layout.addWidget(sounds_group)

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

    def set_scene(self, scene: Optional[SceneModel]):
        """Set the scene to edit."""
        self._sprite = None
        self._scene = scene
        self._game_settings = None

        if scene is None:
            self._title_label.setText(tr("inspector.no_selection"))
            self._stack.setCurrentIndex(0)
            return

        self._title_label.setText(f"🎬 {scene.name}")
        self._stack.setCurrentIndex(2)
        self._refresh_scene()

    def set_game_settings(self, project: ProjectModel):
        """Set the game settings to edit."""
        self._sprite = None
        self._scene = None
        self._project = project
        self._game_settings = project.game

        self._title_label.setText(tr("inspector.game_settings"))
        self._stack.setCurrentIndex(3)
        self._refresh_game_settings()

    def _refresh_sprite(self):
        """Refresh the sprite display."""
        if not self._sprite:
            return

        self._updating = True

        self._title_label.setText(self._sprite.name)
        self._name_edit.setText(self._sprite.name)
        self._class_edit.setText(self._sprite.class_name)
        self._node_type_combo.setCurrentText(self._sprite.node_type)
        self._x_spin.setValue(self._sprite.x)
        self._y_spin.setValue(self._sprite.y)
        self._direction_spin.setValue(self._sprite.direction)
        self._size_spin.setValue(self._sprite.size)
        self._visible_check.setChecked(self._sprite.visible)

        # Costumes
        self._costumes_list.clear()
        self._default_costume_combo.clear()
        for i, costume in enumerate(self._sprite.costumes):
            # Show different icon for code-drawn costumes
            if costume.is_code_drawn():
                display_name = f"🎨 {costume.name}"
                tooltip = f"代码绘制 ({costume.width}x{costume.height})"
            else:
                display_name = f"🖼️ {costume.name}"
                tooltip = costume.path
            item = QListWidgetItem(display_name)
            item.setToolTip(tooltip)
            item.setData(Qt.UserRole, i)
            self._costumes_list.addItem(item)
            self._default_costume_combo.addItem(costume.name)

        if self._sprite.costumes:
            self._default_costume_combo.setCurrentIndex(self._sprite.default_costume)

        # Collision
        self._collision_type_combo.setCurrentText(self._sprite.collision_type)

        # Physics
        self._is_physics_check.setChecked(self._sprite.is_physics)
        self._gravity_x_spin.setValue(self._sprite.gravity_x)
        self._gravity_y_spin.setValue(self._sprite.gravity_y)
        self._friction_spin.setValue(self._sprite.friction)
        self._elasticity_spin.setValue(self._sprite.elasticity)
        self._update_physics_controls_enabled(self._sprite.is_physics)

        # Show/hide type-specific groups
        nt = self._sprite.node_type
        self._camera_group.setVisible(nt == "Camera2D")
        self._light_group.setVisible(nt in ("PointLight2D", "DirectionalLight2D"))
        self._audio_group.setVisible(nt == "AudioPlayer2D")
        self._particle_group.setVisible(nt == "ParticleEmitter2D")
        self._ui_group.setVisible(nt in ("Label", "Button", "ProgressBar", "Panel"))
        self._timer_group.setVisible(nt == "Timer")
        self._tilemap_group.setVisible(nt == "TileMap")
        self._collision_shape_group.setVisible(nt in PHYSICS_NODE_TYPES)

        # Populate type-specific fields
        if nt == "Camera2D":
            self._camera_zoom_spin.setValue(self._sprite.camera_zoom)
            self._camera_smoothing_check.setChecked(self._sprite.camera_smoothing)
            self._camera_smoothing_speed_spin.setValue(self._sprite.camera_smoothing_speed)
            self._camera_follow_edit.setText(self._sprite.camera_follow_target)

        if nt in ("PointLight2D", "DirectionalLight2D"):
            self._light_color_btn.color = self._sprite.light_color
            self._light_energy_spin.setValue(self._sprite.light_energy)
            self._light_radius_spin.setValue(self._sprite.light_radius)
            self._light_shadow_check.setChecked(self._sprite.light_shadow)

        if nt == "AudioPlayer2D":
            self._audio_stream_edit.setText(self._sprite.audio_stream)
            self._audio_volume_spin.setValue(self._sprite.audio_volume)
            self._audio_pitch_spin.setValue(self._sprite.audio_pitch)
            self._audio_autoplay_check.setChecked(self._sprite.audio_autoplay)
            self._audio_loop_check.setChecked(self._sprite.audio_loop)

        if nt == "ParticleEmitter2D":
            self._particle_amount_spin.setValue(self._sprite.particle_amount)
            self._particle_lifetime_spin.setValue(self._sprite.particle_lifetime)
            self._particle_emitting_check.setChecked(self._sprite.particle_emitting)
            self._particle_preset_combo.setCurrentText(self._sprite.particle_preset)

        if nt in ("Label", "Button", "ProgressBar", "Panel"):
            self._ui_text_edit.setText(self._sprite.ui_text)
            self._ui_font_size_spin.setValue(self._sprite.ui_font_size)
            self._ui_text_color_btn.color = self._sprite.ui_text_color
            self._ui_min_spin.setValue(self._sprite.ui_min_value)
            self._ui_max_spin.setValue(self._sprite.ui_max_value)
            self._ui_value_spin.setValue(self._sprite.ui_value)

        if nt == "Timer":
            self._timer_wait_spin.setValue(self._sprite.timer_wait_time)
            self._timer_oneshot_check.setChecked(self._sprite.timer_one_shot)
            self._timer_autostart_check.setChecked(self._sprite.timer_autostart)

        if nt == "TileMap":
            self._tilemap_cellsize_spin.setValue(self._sprite.tilemap_cell_size)

        if nt in PHYSICS_NODE_TYPES:
            self._collision_shape_combo.setCurrentText(self._sprite.collision_shape)
            self._collision_width_spin.setValue(self._sprite.collision_width)
            self._collision_height_spin.setValue(self._sprite.collision_height)
            self._collision_radius_spin.setValue(self._sprite.collision_radius)

        # Specialized editors visibility
        self._tilemap_editor_group.setVisible(nt == "TileMap")
        self._spriteframes_editor_group.setVisible(nt == "AnimatedSprite2D")
        self._path_editor_group.setVisible(nt in ("Path2D", "PathFollow2D", "Line2D"))
        self._nav_editor_group.setVisible(nt == "NavigationAgent2D")

        # Load specialized editor data
        if nt == "TileMap":
            self._tilemap_editor.load_data(
                self._sprite.tilemap_data,
                self._sprite.tilemap_cell_size
            )

        if nt == "AnimatedSprite2D":
            anim_data = self._sprite.properties.get("animations", {})
            if anim_data:
                self._spriteframes_editor.load_animations(anim_data)

        if nt in ("Path2D", "PathFollow2D", "Line2D"):
            self._path_editor.load_data(
                self._sprite.path_points,
                self._sprite.path_loop,
                self._sprite.line_width,
                self._sprite.line_color
            )

        if nt == "NavigationAgent2D":
            nav_grid_data = self._sprite.properties.get("nav_grid", "")
            self._nav_editor.load_data(nav_grid_data)

        self._updating = False

    def _refresh_scene(self):
        """Refresh the scene display."""
        if not self._scene:
            return

        self._updating = True

        self._scene_name_edit.setText(self._scene.name)
        self._bg_color_btn.color = self._scene.background_color
        self._bg_image_edit.setText(self._scene.background_image or "")

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

        # Refresh sounds list
        self._sounds_list.clear()
        if self._project:
            for sound_path in self._project.sounds:
                sound_name = os.path.basename(sound_path)
                item = QListWidgetItem(sound_name)
                item.setToolTip(sound_path)
                item.setData(Qt.UserRole, sound_path)
                self._sounds_list.addItem(item)

        self._updating = False

    def refresh(self):
        """Refresh the current display."""
        if self._sprite:
            self._refresh_sprite()
        elif self._scene:
            self._refresh_scene()
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

    def _on_node_type_changed(self, text: str):
        if self._updating or not self._sprite:
            return
        self._sprite.node_type = text
        # Auto-enable physics for physics body types
        physics_types = {"PhysicsSprite", "StaticBody2D", "RigidBody2D", "KinematicBody2D", "Area2D"}
        is_physics = text in physics_types
        self._sprite.is_physics = is_physics
        self._is_physics_check.setChecked(is_physics)
        self._update_physics_controls_enabled(is_physics)
        self.property_changed.emit(self._sprite, "node_type", text)

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

    def _on_add_code_costume(self):
        """Add a code-drawn costume."""
        if not self._sprite:
            return

        dialog = CodeCostumeDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            idx = self._sprite.add_code_costume(
                data["name"], data["width"], data["height"], data["draw_code"]
            )
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

    def _on_collision_type_changed(self, text: str):
        if self._updating or not self._sprite:
            return
        self._sprite.collision_type = text
        self.property_changed.emit(self._sprite, "collision_type", text)

    def _on_is_physics_changed(self, checked: bool):
        if self._updating or not self._sprite:
            return
        self._sprite.is_physics = checked
        self._update_physics_controls_enabled(checked)
        self.property_changed.emit(self._sprite, "is_physics", checked)

    def _update_physics_controls_enabled(self, enabled: bool):
        """Enable or disable physics property controls based on is_physics."""
        self._gravity_x_spin.setEnabled(enabled)
        self._gravity_y_spin.setEnabled(enabled)
        self._friction_spin.setEnabled(enabled)
        self._elasticity_spin.setEnabled(enabled)

    def _on_gravity_x_changed(self, value: float):
        if self._updating or not self._sprite:
            return
        self._sprite.gravity_x = value
        self.property_changed.emit(self._sprite, "gravity_x", value)

    def _on_gravity_y_changed(self, value: float):
        if self._updating or not self._sprite:
            return
        self._sprite.gravity_y = value
        self.property_changed.emit(self._sprite, "gravity_y", value)

    def _on_friction_changed(self, value: float):
        if self._updating or not self._sprite:
            return
        self._sprite.friction = value
        self.property_changed.emit(self._sprite, "friction", value)

    def _on_elasticity_changed(self, value: float):
        if self._updating or not self._sprite:
            return
        self._sprite.elasticity = value
        self.property_changed.emit(self._sprite, "elasticity", value)

    def _on_typed_prop_changed(self, prop_name: str, value):
        """Generic handler for node-type-specific properties."""
        if self._updating or not self._sprite:
            return
        setattr(self._sprite, prop_name, value)
        self.property_changed.emit(self._sprite, prop_name, value)

    def _on_browse_audio(self):
        """Browse for audio file."""
        if not self._sprite:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.wav *.mp3 *.ogg);;所有文件 (*.*)"
        )
        if path:
            self._audio_stream_edit.setText(path)
            self._sprite.audio_stream = path
            self.property_changed.emit(self._sprite, "audio_stream", path)

    def _on_tilemap_data_changed(self, data: str):
        """Handle tilemap editor data change."""
        if self._updating or not self._sprite:
            return
        self._sprite.tilemap_data = data
        self.property_changed.emit(self._sprite, "tilemap_data", data)

    def _on_spriteframes_data_changed(self, data: dict):
        """Handle sprite frames editor data change."""
        if self._updating or not self._sprite:
            return
        self._sprite.properties["animations"] = data
        self.property_changed.emit(self._sprite, "animations", data)

    def _on_path_data_changed(self, points, loop, width, color):
        """Handle path editor data change."""
        if self._updating or not self._sprite:
            return
        self._sprite.path_points = points
        self._sprite.path_loop = loop
        self._sprite.line_width = width
        if isinstance(color, tuple):
            self._sprite.line_color = color
        self.property_changed.emit(self._sprite, "path_points", points)

    def _on_nav_data_changed(self, data: str):
        """Handle navigation grid editor data change."""
        if self._updating or not self._sprite:
            return
        self._sprite.properties["nav_grid"] = data
        self.property_changed.emit(self._sprite, "nav_grid", data)

    def _on_costume_context_menu(self, pos):
        if not self._sprite:
            return

        item = self._costumes_list.itemAt(pos)
        if not item:
            return

        index = item.data(Qt.UserRole)
        menu = QMenu(self)

        # Add edit option for code-drawn costumes
        if index is not None and index < len(self._sprite.costumes):
            costume = self._sprite.costumes[index]
            if costume.is_code_drawn():
                edit_action = QAction("编辑绘制代码...", self)
                edit_action.triggered.connect(lambda: self._edit_code_costume(item))
                menu.addAction(edit_action)
                menu.addSeparator()

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

    def _edit_code_costume(self, item):
        """Edit a code-drawn costume."""
        if not self._sprite:
            return
        index = item.data(Qt.UserRole)
        if index is None or index >= len(self._sprite.costumes):
            return

        costume = self._sprite.costumes[index]
        if not costume.is_code_drawn():
            return

        dialog = CodeCostumeDialog(self, costume)
        if dialog.exec():
            data = dialog.get_data()
            costume.name = data["name"]
            costume.width = data["width"]
            costume.height = data["height"]
            costume.draw_code = data["draw_code"]
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

    # Scene property change handlers
    def _on_scene_name_changed(self, text: str):
        if self._updating or not self._scene:
            return
        self._scene.name = text
        self._title_label.setText(f"🎬 {text}")
        self.scene_property_changed.emit(self._scene, "name", text)

    def _on_bg_color_changed(self, color: tuple):
        if self._updating or not self._scene:
            return
        self._scene.background_color = color
        self.scene_property_changed.emit(self._scene, "background_color", color)

    def _on_browse_bg_image(self):
        if not self._scene:
            return

        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.select_bg_image"), "",
            tr("dialog.image_filter")
        )

        if path:
            self._scene.background_image = path
            self._bg_image_edit.setText(path)
            self.scene_property_changed.emit(self._scene, "background_image", path)

    def _on_clear_bg_image(self):
        if not self._scene:
            return
        self._scene.background_image = None
        self._bg_image_edit.setText("")
        self.scene_property_changed.emit(self._scene, "background_image", None)

    # Sound management methods
    def _on_add_sound(self):
        """Add a sound file to the project."""
        if not self._project:
            return

        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.select_sound"), "",
            tr("dialog.sound_filter")
        )

        if path and path not in self._project.sounds:
            self._project.sounds.append(path)
            self._refresh_game_settings()
            self.game_property_changed.emit("sounds", self._project.sounds)

    def _on_sound_context_menu(self, pos):
        """Show context menu for sound item."""
        item = self._sounds_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        remove_action = QAction(tr("inspector.remove_sound"), self)
        remove_action.triggered.connect(lambda: self._remove_sound(item))
        menu.addAction(remove_action)

        menu.exec_(self._sounds_list.mapToGlobal(pos))

    def _remove_sound(self, item):
        """Remove a sound from the project."""
        if not self._project:
            return

        sound_path = item.data(Qt.UserRole)
        if sound_path in self._project.sounds:
            self._project.sounds.remove(sound_path)
            self._refresh_game_settings()
            self.game_property_changed.emit("sounds", self._project.sounds)
