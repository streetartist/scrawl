"""
Code Costume Dialog

Dialog for creating costumes using pygame drawing code.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QPlainTextEdit, QPushButton,
    QLabel, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


DEFAULT_DRAW_CODE = '''# 在 surface 上绘制造型
# surface 是一个 pygame.Surface 对象，大小为 (width, height)
# 示例：绘制一个圆形
pygame.draw.circle(surface, (255, 200, 0), (width//2, height//2), min(width, height)//2)
'''


class CodeCostumeDialog(QDialog):
    """Dialog for creating a code-drawn costume."""

    def __init__(self, parent=None, costume_data=None):
        super().__init__(parent)
        self.setWindowTitle("代码绘制造型")
        self.setMinimumSize(500, 450)

        self._costume_data = costume_data  # For editing existing costume
        self._setup_ui()

        if costume_data:
            self._load_costume_data(costume_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Basic info group
        info_group = QGroupBox("基本信息")
        info_layout = QFormLayout(info_group)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("例如: bird, pipe, ground")
        info_layout.addRow("造型名称:", self._name_edit)

        # Size
        size_widget = QHBoxLayout()
        self._width_spin = QSpinBox()
        self._width_spin.setRange(1, 1024)
        self._width_spin.setValue(32)
        size_widget.addWidget(QLabel("宽度:"))
        size_widget.addWidget(self._width_spin)

        self._height_spin = QSpinBox()
        self._height_spin.setRange(1, 1024)
        self._height_spin.setValue(32)
        size_widget.addWidget(QLabel("高度:"))
        size_widget.addWidget(self._height_spin)
        size_widget.addStretch()

        info_layout.addRow("尺寸:", size_widget)
        layout.addWidget(info_group)

        # Code group
        code_group = QGroupBox("绘制代码 (pygame)")
        code_layout = QVBoxLayout(code_group)

        hint = QLabel(
            "可用变量: surface (pygame.Surface), width, height\n"
            "可用模块: pygame (已导入)"
        )
        hint.setStyleSheet("color: #888; font-size: 11px;")
        code_layout.addWidget(hint)

        self._code_edit = QPlainTextEdit()
        self._code_edit.setPlaceholderText(DEFAULT_DRAW_CODE)
        font = QFont("Consolas", 10)
        self._code_edit.setFont(font)
        self._code_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #555;
            }
        """)
        code_layout.addWidget(self._code_edit, 1)

        layout.addWidget(code_group, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def _load_costume_data(self, costume_data):
        """Load existing costume data for editing."""
        self._name_edit.setText(costume_data.name)
        self._width_spin.setValue(costume_data.width)
        self._height_spin.setValue(costume_data.height)
        self._code_edit.setPlainText(costume_data.draw_code)

    def get_data(self) -> dict:
        """Get the costume data from the dialog."""
        code = self._code_edit.toPlainText().strip()
        if not code:
            code = DEFAULT_DRAW_CODE.strip()

        return {
            "name": self._name_edit.text().strip() or "costume",
            "width": self._width_spin.value(),
            "height": self._height_spin.value(),
            "draw_code": code
        }
