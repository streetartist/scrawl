"""
SpriteFrames Editor

Visual editor for managing sprite frame animations.
Supports adding frames, creating animations, and previewing.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QSpinBox, QCheckBox,
    QGroupBox, QFormLayout, QInputDialog, QFileDialog,
    QComboBox, QSplitter, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QPixmap, QIcon
from typing import Optional, Dict, List
import os


class SpriteFramesEditor(QWidget):
    """Editor for managing animated sprite frame sets."""

    data_changed = Signal(dict)  # {anim_name: {frames: [...], fps: N, loop: bool}}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animations: Dict[str, dict] = {}
        self._current_anim: Optional[str] = None
        self._preview_frame = 0
        self._preview_timer = QTimer(self)
        self._preview_timer.timeout.connect(self._advance_frame)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # --- Animation list ---
        anim_group = QGroupBox("动画列表")
        ag_layout = QVBoxLayout(anim_group)

        self._anim_combo = QComboBox()
        self._anim_combo.currentTextChanged.connect(self._on_anim_selected)
        ag_layout.addWidget(self._anim_combo)

        anim_btn_row = QHBoxLayout()
        add_anim_btn = QPushButton("添加动画")
        add_anim_btn.clicked.connect(self._add_animation)
        anim_btn_row.addWidget(add_anim_btn)

        del_anim_btn = QPushButton("删除动画")
        del_anim_btn.clicked.connect(self._delete_animation)
        anim_btn_row.addWidget(del_anim_btn)

        rename_anim_btn = QPushButton("重命名")
        rename_anim_btn.clicked.connect(self._rename_animation)
        anim_btn_row.addWidget(rename_anim_btn)
        ag_layout.addLayout(anim_btn_row)

        layout.addWidget(anim_group)

        # --- Animation settings ---
        settings_group = QGroupBox("动画设置")
        sg_layout = QFormLayout(settings_group)

        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(1, 120)
        self._fps_spin.setValue(12)
        self._fps_spin.valueChanged.connect(self._on_fps_changed)
        sg_layout.addRow("帧率(FPS):", self._fps_spin)

        self._loop_check = QCheckBox()
        self._loop_check.setChecked(True)
        self._loop_check.toggled.connect(self._on_loop_changed)
        sg_layout.addRow("循环:", self._loop_check)

        layout.addWidget(settings_group)

        # --- Frame list ---
        frames_group = QGroupBox("帧列表")
        fg_layout = QVBoxLayout(frames_group)

        self._frame_list = QListWidget()
        self._frame_list.setIconSize(QSize(48, 48))
        self._frame_list.setMinimumHeight(100)
        fg_layout.addWidget(self._frame_list)

        frame_btn_row = QHBoxLayout()
        add_frame_btn = QPushButton("添加帧")
        add_frame_btn.clicked.connect(self._add_frames)
        frame_btn_row.addWidget(add_frame_btn)

        del_frame_btn = QPushButton("删除帧")
        del_frame_btn.clicked.connect(self._delete_frame)
        frame_btn_row.addWidget(del_frame_btn)

        move_up_btn = QPushButton("↑上移")
        move_up_btn.clicked.connect(self._move_frame_up)
        frame_btn_row.addWidget(move_up_btn)

        move_down_btn = QPushButton("↓下移")
        move_down_btn.clicked.connect(self._move_frame_down)
        frame_btn_row.addWidget(move_down_btn)

        fg_layout.addLayout(frame_btn_row)
        layout.addWidget(frames_group)

        # --- Preview ---
        preview_group = QGroupBox("预览")
        pg_layout = QVBoxLayout(preview_group)

        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setMinimumSize(96, 96)
        self._preview_label.setStyleSheet("background: #333; border: 1px solid #555;")
        pg_layout.addWidget(self._preview_label)

        preview_btn_row = QHBoxLayout()
        self._play_btn = QPushButton("▶ 播放")
        self._play_btn.setCheckable(True)
        self._play_btn.toggled.connect(self._on_toggle_preview)
        preview_btn_row.addWidget(self._play_btn)

        self._frame_label = QLabel("帧: 0/0")
        preview_btn_row.addWidget(self._frame_label)
        pg_layout.addLayout(preview_btn_row)

        layout.addWidget(preview_group)
        layout.addStretch()

    def _current_anim_data(self) -> Optional[dict]:
        if self._current_anim and self._current_anim in self._animations:
            return self._animations[self._current_anim]
        return None

    def _on_anim_selected(self, name: str):
        self._current_anim = name
        self._stop_preview()
        self._refresh_frames()

    def _refresh_frames(self):
        self._frame_list.clear()
        data = self._current_anim_data()
        if not data:
            return

        self._fps_spin.blockSignals(True)
        self._fps_spin.setValue(data.get("fps", 12))
        self._fps_spin.blockSignals(False)

        self._loop_check.blockSignals(True)
        self._loop_check.setChecked(data.get("loop", True))
        self._loop_check.blockSignals(False)

        for i, frame_path in enumerate(data.get("frames", [])):
            fname = os.path.basename(frame_path)
            item = QListWidgetItem(f"{i}: {fname}")
            item.setData(Qt.UserRole, frame_path)
            if os.path.exists(frame_path):
                pixmap = QPixmap(frame_path)
                if not pixmap.isNull():
                    item.setIcon(QIcon(pixmap.scaled(
                        48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )))
            self._frame_list.addItem(item)

    def _add_animation(self):
        name, ok = QInputDialog.getText(self, "添加动画", "动画名称:", text="idle")
        if ok and name and name not in self._animations:
            self._animations[name] = {"frames": [], "fps": 12, "loop": True}
            self._anim_combo.addItem(name)
            self._anim_combo.setCurrentText(name)
            self._emit_change()

    def _delete_animation(self):
        if not self._current_anim:
            return
        self._animations.pop(self._current_anim, None)
        idx = self._anim_combo.currentIndex()
        self._anim_combo.removeItem(idx)
        self._emit_change()

    def _rename_animation(self):
        if not self._current_anim:
            return
        new_name, ok = QInputDialog.getText(
            self, "重命名", "新名称:", text=self._current_anim
        )
        if ok and new_name and new_name != self._current_anim:
            data = self._animations.pop(self._current_anim)
            self._animations[new_name] = data
            idx = self._anim_combo.currentIndex()
            self._anim_combo.setItemText(idx, new_name)
            self._current_anim = new_name
            self._emit_change()

    def _add_frames(self):
        if not self._current_anim:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择帧图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)"
        )
        if paths:
            data = self._current_anim_data()
            if data is not None:
                data["frames"].extend(paths)
                self._refresh_frames()
                self._emit_change()

    def _delete_frame(self):
        data = self._current_anim_data()
        if not data:
            return
        idx = self._frame_list.currentRow()
        if 0 <= idx < len(data["frames"]):
            data["frames"].pop(idx)
            self._refresh_frames()
            self._emit_change()

    def _move_frame_up(self):
        data = self._current_anim_data()
        if not data:
            return
        idx = self._frame_list.currentRow()
        if idx > 0:
            frames = data["frames"]
            frames[idx - 1], frames[idx] = frames[idx], frames[idx - 1]
            self._refresh_frames()
            self._frame_list.setCurrentRow(idx - 1)
            self._emit_change()

    def _move_frame_down(self):
        data = self._current_anim_data()
        if not data:
            return
        idx = self._frame_list.currentRow()
        frames = data["frames"]
        if 0 <= idx < len(frames) - 1:
            frames[idx], frames[idx + 1] = frames[idx + 1], frames[idx]
            self._refresh_frames()
            self._frame_list.setCurrentRow(idx + 1)
            self._emit_change()

    def _on_fps_changed(self, value: int):
        data = self._current_anim_data()
        if data:
            data["fps"] = value
            self._emit_change()

    def _on_loop_changed(self, checked: bool):
        data = self._current_anim_data()
        if data:
            data["loop"] = checked
            self._emit_change()

    def _on_toggle_preview(self, playing: bool):
        if playing:
            self._start_preview()
        else:
            self._stop_preview()

    def _start_preview(self):
        data = self._current_anim_data()
        if not data or not data["frames"]:
            self._play_btn.setChecked(False)
            return
        fps = data.get("fps", 12)
        self._preview_frame = 0
        self._preview_timer.start(max(16, 1000 // fps))
        self._show_preview_frame()

    def _stop_preview(self):
        self._preview_timer.stop()
        self._play_btn.setChecked(False)

    def _advance_frame(self):
        data = self._current_anim_data()
        if not data or not data["frames"]:
            self._stop_preview()
            return
        self._preview_frame += 1
        if self._preview_frame >= len(data["frames"]):
            if data.get("loop", True):
                self._preview_frame = 0
            else:
                self._stop_preview()
                return
        self._show_preview_frame()

    def _show_preview_frame(self):
        data = self._current_anim_data()
        if not data or not data["frames"]:
            return
        idx = self._preview_frame
        frames = data["frames"]
        if 0 <= idx < len(frames):
            path = frames[idx]
            if os.path.exists(path):
                pixmap = QPixmap(path).scaled(
                    96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self._preview_label.setPixmap(pixmap)
            self._frame_label.setText(f"帧: {idx + 1}/{len(frames)}")

    def _emit_change(self):
        self.data_changed.emit(dict(self._animations))

    # --- Public API ---

    def load_animations(self, data: Dict[str, dict]):
        """Load animation data."""
        self._animations = dict(data)
        self._anim_combo.clear()
        for name in self._animations:
            self._anim_combo.addItem(name)
        if self._animations:
            first = next(iter(self._animations))
            self._anim_combo.setCurrentText(first)
        self._refresh_frames()

    def get_animations(self) -> Dict[str, dict]:
        return dict(self._animations)
