"""
Settings Dialog

Dialog for configuring IDE settings including editor font.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSpinBox, QComboBox, QLineEdit,
    QDialogButtonBox, QPlainTextEdit
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFontDatabase

from .settings import Settings
from .i18n import tr

# Fonts known to have issues with DirectWrite on Windows
PROBLEMATIC_FONTS = {"Fixedsys", "Terminal", "System", "MS Sans Serif", "MS Serif"}


class SettingsDialog(QDialog):
    """Settings dialog for IDE configuration."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = Settings()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(tr("dialog.settings.title"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Editor settings group
        editor_group = QGroupBox(tr("dialog.settings.editor"))
        editor_layout = QVBoxLayout(editor_group)

        # Font family
        font_layout = QHBoxLayout()
        font_label = QLabel(tr("dialog.settings.font_family"))
        self._font_combo = QComboBox()
        self._populate_font_combo()
        self._font_combo.currentTextChanged.connect(self._on_font_changed)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self._font_combo, 1)
        editor_layout.addLayout(font_layout)

        # Font size
        size_layout = QHBoxLayout()
        size_label = QLabel(tr("dialog.settings.font_size"))
        self._size_spin = QSpinBox()
        self._size_spin.setRange(8, 32)
        self._size_spin.setSuffix(" pt")
        self._size_spin.valueChanged.connect(self._on_font_changed)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self._size_spin)
        size_layout.addStretch()
        editor_layout.addLayout(size_layout)

        # Preview
        preview_label = QLabel(tr("dialog.settings.preview"))
        editor_layout.addWidget(preview_label)

        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMaximumHeight(120)
        self._preview.setPlainText(self._get_preview_text())
        editor_layout.addWidget(self._preview)

        layout.addWidget(editor_group)

        # AI settings group
        ai_group = QGroupBox(tr("dialog.settings.ai"))
        ai_layout = QVBoxLayout(ai_group)

        # API Key
        key_layout = QHBoxLayout()
        key_label = QLabel(tr("dialog.settings.ai_key"))
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.Password)
        self._api_key_edit.setPlaceholderText("sk-...")
        key_layout.addWidget(key_label)
        key_layout.addWidget(self._api_key_edit, 1)
        ai_layout.addLayout(key_layout)

        # Endpoint
        endpoint_layout = QHBoxLayout()
        endpoint_label = QLabel(tr("dialog.settings.ai_endpoint"))
        self._endpoint_edit = QLineEdit()
        self._endpoint_edit.setPlaceholderText("https://api.openai.com/v1")
        endpoint_layout.addWidget(endpoint_label)
        endpoint_layout.addWidget(self._endpoint_edit, 1)
        ai_layout.addLayout(endpoint_layout)

        # Model
        model_layout = QHBoxLayout()
        model_label = QLabel(tr("dialog.settings.ai_model"))
        self._model_edit = QLineEdit()
        self._model_edit.setPlaceholderText("gpt-4o-mini")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self._model_edit, 1)
        ai_layout.addLayout(model_layout)

        layout.addWidget(ai_group)
        layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(button_box)

    def _get_preview_text(self) -> str:
        """Get preview text for font display."""
        return '''def hello_world():
    """示例代码 - Sample Code"""
    print("Hello, 世界!")
    for i in range(10):
        yield i * 2'''

    def _populate_font_combo(self):
        """Populate font combo with compatible monospace fonts."""
        all_fonts = QFontDatabase.families()
        monospace_fonts = []

        # Preferred fonts to show first
        preferred = [
            "Cascadia Code", "Cascadia Mono", "JetBrains Mono",
            "Fira Code", "Source Code Pro", "Consolas",
            "Courier New", "DejaVu Sans Mono", "Monaco"
        ]

        for family in all_fonts:
            if family in PROBLEMATIC_FONTS:
                continue
            # Check if font is monospace using multiple methods
            if QFontDatabase.isFixedPitch(family):
                monospace_fonts.append(family)
            elif family in preferred:
                # Include preferred fonts even if isFixedPitch fails
                monospace_fonts.append(family)

        # Sort with preferred fonts first
        def sort_key(name):
            if name in preferred:
                return (0, preferred.index(name))
            return (1, name.lower())

        monospace_fonts = list(set(monospace_fonts))  # Remove duplicates
        monospace_fonts.sort(key=sort_key)
        self._font_combo.addItems(monospace_fonts)

    def _load_settings(self):
        """Load current settings into the dialog."""
        # Editor settings
        font_family = self._settings.get_font_family()
        font_size = self._settings.get_font_size()

        index = self._font_combo.findText(font_family)
        if index >= 0:
            self._font_combo.setCurrentIndex(index)
        self._size_spin.setValue(font_size)
        self._update_preview()

        # AI settings
        self._api_key_edit.setText(self._settings.get_ai_api_key())
        self._endpoint_edit.setText(self._settings.get_ai_endpoint())
        self._model_edit.setText(self._settings.get_ai_model())

    def _on_font_changed(self):
        """Handle font change."""
        self._update_preview()

    def _update_preview(self):
        """Update the preview with current font settings."""
        font_family = self._font_combo.currentText()
        font_size = self._size_spin.value()
        if not font_family:
            return
        # Use stylesheet to set font (setFont doesn't work with stylesheets)
        self._preview.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #555;
                font-family: "{font_family}";
                font-size: {font_size}pt;
            }}
        """)

    def _apply_settings(self):
        """Apply settings without closing dialog."""
        # Editor settings
        self._settings.set_font_family(self._font_combo.currentText())
        self._settings.set_font_size(self._size_spin.value())

        # AI settings
        self._settings.set_ai_api_key(self._api_key_edit.text())
        self._settings.set_ai_endpoint(self._endpoint_edit.text() or "https://api.openai.com/v1")
        self._settings.set_ai_model(self._model_edit.text() or "gpt-4o-mini")

        self.settings_changed.emit()

    def _on_accept(self):
        """Handle OK button."""
        self._apply_settings()
        self.accept()
