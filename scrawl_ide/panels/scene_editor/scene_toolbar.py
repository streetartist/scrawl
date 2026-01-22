"""
Scene Toolbar

Toolbar for scene editing tools and actions.
"""

from PySide6.QtWidgets import (
    QToolBar, QToolButton, QButtonGroup, QLabel, QSpinBox,
    QComboBox, QWidget, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction

from core.i18n import tr


class SceneToolbar(QToolBar):
    """Toolbar for scene editing controls."""

    tool_changed = Signal(str)  # Tool name
    zoom_changed = Signal(float)  # Zoom factor
    grid_toggled = Signal(bool)
    snap_toggled = Signal(bool)
    grid_size_changed = Signal(int)  # Grid size in pixels

    def __init__(self, parent=None):
        super().__init__("Scene Tools", parent)

        self._current_tool = "select"
        self._setup_ui()

    def _setup_ui(self):
        """Set up the toolbar UI."""
        self.setIconSize(QSize(20, 20))
        self.setMovable(False)

        # Tool buttons group
        self._tool_group = QButtonGroup(self)
        self._tool_group.setExclusive(True)

        # Select tool
        self._select_btn = QToolButton()
        self._select_btn.setText(tr("scene.toolbar.select"))
        self._select_btn.setCheckable(True)
        self._select_btn.setChecked(True)
        self._select_btn.setToolTip(tr("scene.toolbar.select.tip"))
        self._tool_group.addButton(self._select_btn)
        self.addWidget(self._select_btn)

        # Pan tool
        self._pan_btn = QToolButton()
        self._pan_btn.setText(tr("scene.toolbar.pan"))
        self._pan_btn.setCheckable(True)
        self._pan_btn.setToolTip(tr("scene.toolbar.pan.tip"))
        self._tool_group.addButton(self._pan_btn)
        self.addWidget(self._pan_btn)

        self.addSeparator()

        # Zoom controls
        zoom_label = QLabel(" " + tr("scene.toolbar.zoom") + " ")
        self.addWidget(zoom_label)

        self._zoom_combo = QComboBox()
        self._zoom_combo.addItems(["25%", "50%", "75%", "100%", "150%", "200%", "400%"])
        self._zoom_combo.setCurrentText("100%")
        self._zoom_combo.setEditable(True)
        self._zoom_combo.setMinimumWidth(80)
        self._zoom_combo.currentTextChanged.connect(self._on_zoom_changed)
        self.addWidget(self._zoom_combo)

        # Zoom buttons
        zoom_in_btn = QToolButton()
        zoom_in_btn.setText("+")
        zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        zoom_in_btn.clicked.connect(lambda: self._adjust_zoom(1.25))
        self.addWidget(zoom_in_btn)

        zoom_out_btn = QToolButton()
        zoom_out_btn.setText("-")
        zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        zoom_out_btn.clicked.connect(lambda: self._adjust_zoom(0.8))
        self.addWidget(zoom_out_btn)

        zoom_fit_btn = QToolButton()
        zoom_fit_btn.setText(tr("scene.toolbar.fit"))
        zoom_fit_btn.setToolTip("Fit to View")
        zoom_fit_btn.clicked.connect(lambda: self.zoom_changed.emit(-1))  # -1 = fit
        self.addWidget(zoom_fit_btn)

        self.addSeparator()

        # Grid toggle
        self._grid_btn = QToolButton()
        self._grid_btn.setText(tr("scene.toolbar.grid"))
        self._grid_btn.setCheckable(True)
        self._grid_btn.setChecked(True)
        self._grid_btn.setToolTip("Toggle Grid (G)")
        self._grid_btn.toggled.connect(self.grid_toggled.emit)
        self.addWidget(self._grid_btn)

        # Snap toggle
        self._snap_btn = QToolButton()
        self._snap_btn.setText(tr("scene.toolbar.snap"))
        self._snap_btn.setCheckable(True)
        self._snap_btn.setToolTip("Snap to Grid (S)")
        self._snap_btn.toggled.connect(self.snap_toggled.emit)
        self.addWidget(self._snap_btn)

        self.addSeparator()

        # Grid size
        grid_label = QLabel(" " + tr("scene.toolbar.grid_size") + " ")
        self.addWidget(grid_label)

        self._grid_spin = QSpinBox()
        self._grid_spin.setRange(8, 128)
        self._grid_spin.setValue(32)
        self._grid_spin.setSuffix(" px")
        self._grid_spin.valueChanged.connect(self.grid_size_changed.emit)
        self.addWidget(self._grid_spin)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy(),
                            spacer.sizePolicy().verticalPolicy())
        self.addWidget(spacer)

        # Connect tool buttons
        self._select_btn.clicked.connect(lambda: self._set_tool("select"))
        self._pan_btn.clicked.connect(lambda: self._set_tool("pan"))

    def _set_tool(self, tool: str):
        """Set the current tool."""
        self._current_tool = tool
        self.tool_changed.emit(tool)

    def _on_zoom_changed(self, text: str):
        """Handle zoom combo change."""
        try:
            # Parse percentage
            value = float(text.replace('%', '').strip())
            self.zoom_changed.emit(value / 100.0)
        except ValueError:
            pass

    def _adjust_zoom(self, factor: float):
        """Adjust zoom by a factor."""
        try:
            current = float(self._zoom_combo.currentText().replace('%', ''))
            new_zoom = current * factor
            new_zoom = max(10, min(500, new_zoom))  # Clamp
            self._zoom_combo.setCurrentText(f"{int(new_zoom)}%")
        except ValueError:
            pass

    def set_zoom(self, factor: float):
        """Set the zoom display."""
        self._zoom_combo.blockSignals(True)
        self._zoom_combo.setCurrentText(f"{int(factor * 100)}%")
        self._zoom_combo.blockSignals(False)

    @property
    def current_tool(self) -> str:
        return self._current_tool

    @property
    def grid_size(self) -> int:
        return self._grid_spin.value()

    @property
    def grid_enabled(self) -> bool:
        return self._grid_btn.isChecked()

    @property
    def snap_enabled(self) -> bool:
        return self._snap_btn.isChecked()
