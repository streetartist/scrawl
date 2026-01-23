"""
AI Chat Panel

Chat interface for AI code assistance with code modification support.
"""

import re
from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor

from core.ai_service import AIService
from core.i18n import tr

if TYPE_CHECKING:
    from models import ProjectModel


class AIChatPanel(QWidget):
    """AI chat panel for code assistance."""

    code_generated = Signal(str)  # Emitted when AI generates code
    code_applied = Signal()  # Emitted when code is applied to a sprite/scene

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ai_service = AIService(self)
        self._current_response = ""
        self._context = ""
        self._project: Optional['ProjectModel'] = None
        self._main_window = None
        self._streaming_started = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Chat display
        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        self._chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #555;
                font-size: 12pt;
            }
        """)
        layout.addWidget(self._chat_display, 1)

        # Input area
        input_layout = QHBoxLayout()
        self._input_edit = QLineEdit()
        self._input_edit.setPlaceholderText(tr("ai.input_placeholder"))
        self._input_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #555;
                padding: 6px;
                font-size: 12pt;
            }
        """)
        self._input_edit.returnPressed.connect(self._send_message)
        input_layout.addWidget(self._input_edit, 1)

        self._send_btn = QPushButton(tr("ai.send"))
        self._send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self._send_btn)

        self._apply_btn = QPushButton(tr("ai.apply"))
        self._apply_btn.clicked.connect(self._apply_code)
        self._apply_btn.setEnabled(False)
        input_layout.addWidget(self._apply_btn)

        self._clear_btn = QPushButton(tr("ai.clear"))
        self._clear_btn.clicked.connect(self._clear_chat)
        input_layout.addWidget(self._clear_btn)

        layout.addLayout(input_layout)

    def _connect_signals(self):
        """Connect AI service signals."""
        self._ai_service.response_chunk.connect(self._on_response_chunk)
        self._ai_service.response_done.connect(self._on_response_done)
        self._ai_service.error_occurred.connect(self._on_error)

    def load_engine_source(self, engine_path: str):
        """Load engine source for AI context."""
        self._ai_service.load_engine_source(engine_path)

    def set_context(self, context: str):
        """Set current context (sprite/scene info)."""
        self._context = context

    def set_project(self, project: 'ProjectModel', main_window):
        """Set project reference for code modification."""
        self._project = project
        self._main_window = main_window

    def _send_message(self):
        """Send user message."""
        text = self._input_edit.text().strip()
        if not text or self._ai_service.is_busy():
            return

        self._input_edit.clear()
        self._append_message("user", text)
        self._current_response = ""
        self._streaming_started = False
        self._ai_service.send_message(text, self._context)
        self._send_btn.setEnabled(False)

    def _on_response_chunk(self, chunk: str):
        """Handle response chunk."""
        if not self._streaming_started:
            # Start AI response with label
            self._chat_display.append('<span style="color: #81C784;"><b>AI:</b> </span>')
            self._streaming_started = True
        self._current_response += chunk
        # Insert chunk at cursor position
        cursor = self._chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(chunk)
        self._scroll_to_bottom()

    def _on_response_done(self):
        """Handle response completion."""
        self._ai_service.add_assistant_message(self._current_response)
        self._send_btn.setEnabled(True)
        # Add newline after streaming response
        self._chat_display.append("")
        # Show pending changes preview
        self._show_pending_changes()

    def _on_error(self, error: str):
        """Handle error."""
        self._append_message("error", error)
        self._send_btn.setEnabled(True)

    def _append_message(self, role: str, content: str, is_html: bool = False):
        """Append message to chat display."""
        if role == "user":
            html = f'<p style="color: #4FC3F7;"><b>你:</b> {content}</p>'
        elif role == "error":
            html = f'<p style="color: #FF6B6B;"><b>错误:</b> {content}</p>'
        elif is_html:
            html = f'<p style="color: #81C784;"><b>AI:</b></p>{content}'
        else:
            html = f'<p style="color: #81C784;"><b>AI:</b> {content}</p>'
        self._chat_display.append(html)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        scrollbar = self._chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _format_response(self, text: str) -> str:
        """Format response with code highlighting."""
        # Simple code block formatting
        text = re.sub(r'```python\n(.*?)```', r'<pre style="background:#2D2D2D;padding:8px;">\1</pre>', text, flags=re.DOTALL)
        text = re.sub(r'```\n(.*?)```', r'<pre style="background:#2D2D2D;padding:8px;">\1</pre>', text, flags=re.DOTALL)
        text = text.replace('\n', '<br>')
        return text

    def _extract_code_blocks(self) -> list:
        """Extract code blocks from response."""
        pattern = r'```python(?::(\w+):([^\n]+))?\n(.*?)```'
        matches = re.findall(pattern, self._current_response, re.DOTALL)
        return matches

    def _extract_json_blocks(self) -> list:
        """Extract JSON property blocks from response."""
        pattern = r'```json:(\w+):([^\n]+)\n(.*?)```'
        matches = re.findall(pattern, self._current_response, re.DOTALL)
        return matches

    def _show_pending_changes(self):
        """Show preview of pending changes from AI response."""
        import json
        pending = []

        # Check code blocks
        code_blocks = self._extract_code_blocks()
        for target_type, target_id, code in code_blocks:
            if target_type and target_id:
                pending.append(f"代码修改 → {target_type}:{target_id.strip()}")

        # Check property blocks
        json_blocks = self._extract_json_blocks()
        for target_type, target_id, json_str in json_blocks:
            if target_type and target_id:
                try:
                    props = json.loads(json_str.strip())
                    prop_names = ", ".join(props.keys())
                    pending.append(f"属性修改 → {target_type}:{target_id.strip()} ({prop_names})")
                except json.JSONDecodeError:
                    pending.append(f"属性修改 → {target_type}:{target_id.strip()}")

        if pending:
            msg = "📋 待应用的修改：\n" + "\n".join(f"  • {item}" for item in pending)
            self._chat_display.append(f'<p style="color: #FFA726;">{msg.replace(chr(10), "<br>")}</p>')
            self._apply_btn.setEnabled(True)
            self._scroll_to_bottom()

    def _display_formatted_response(self):
        """Display the formatted response in chat."""
        formatted = self._format_response(self._current_response)
        self._append_message("assistant", formatted, is_html=True)

    def _clear_chat(self):
        """Clear chat history."""
        self._chat_display.clear()
        self._ai_service.clear_history()
        self._current_response = ""
        self._apply_btn.setEnabled(False)

    def _apply_code(self):
        """Apply code and properties from AI response."""
        if not self._project:
            self._append_message("error", "未加载项目")
            return

        applied_items = []

        # Apply code blocks
        code_blocks = self._extract_code_blocks()
        for target_type, target_id, code in code_blocks:
            code = code.strip()
            if not target_type or not target_id:
                continue
            target_id = target_id.strip()
            if self._apply_code_to_target(target_type, target_id, code):
                applied_items.append(f"代码 → {target_type}:{target_id}")

        # Apply property blocks
        json_blocks = self._extract_json_blocks()
        for target_type, target_id, json_str in json_blocks:
            json_str = json_str.strip()
            if not target_type or not target_id:
                continue
            target_id = target_id.strip()
            props_applied = self._apply_properties(target_type, target_id, json_str)
            if props_applied:
                applied_items.append(f"属性 → {target_type}:{target_id} ({props_applied})")

        if applied_items:
            msg = "已应用修改：\n" + "\n".join(f"  • {item}" for item in applied_items)
            self._append_message("assistant", msg)
            self.code_applied.emit()
            self._apply_btn.setEnabled(False)
        else:
            self._append_message("error", "未能应用任何修改，请确保AI指定了目标")

    def _apply_code_to_target(self, target_type: str, target_id: str, code: str) -> bool:
        """Apply code to a specific target."""
        if target_type == "sprite":
            return self._apply_to_sprite(target_id, code)
        elif target_type == "scene":
            return self._apply_to_scene(target_id, code)
        return False

    def _apply_to_sprite(self, target_id: str, code: str) -> bool:
        """Apply code to a sprite by id or name."""
        for scene in self._project.scenes:
            for sprite in scene.sprites:
                if sprite.id == target_id or sprite.name == target_id:
                    sprite.code = code
                    self._update_editor(f"sprite:{sprite.id}", code)
                    if self._main_window:
                        self._main_window.project.mark_modified()
                    return True
        return False

    def _apply_to_scene(self, target_id: str, code: str) -> bool:
        """Apply code to a scene by id or name."""
        for scene in self._project.scenes:
            if scene.id == target_id or scene.name == target_id:
                scene.code = code
                self._update_editor(f"scene:{scene.id}", code)
                if self._main_window:
                    self._main_window.project.mark_modified()
                return True
        return False

    def _update_editor(self, tab_id: str, code: str):
        """Update open editor tab with new code."""
        if not self._main_window:
            return
        code_tabs = self._main_window.code_tabs
        for i in range(code_tabs.count()):
            widget = code_tabs.widget(i)
            if hasattr(widget, 'tab_id') and widget.tab_id == tab_id:
                widget.set_text(code)
                break

    def _apply_properties(self, target_type: str, target_id: str, json_str: str) -> str:
        """Apply properties from JSON to target. Returns applied props or empty string."""
        import json
        try:
            props = json.loads(json_str)
        except json.JSONDecodeError:
            return ""

        if target_type == "sprite":
            return self._apply_sprite_props(target_id, props)
        elif target_type == "scene":
            return self._apply_scene_props(target_id, props)
        elif target_type == "game":
            return self._apply_game_props(props)
        return ""

    def _apply_sprite_props(self, target_id: str, props: dict) -> str:
        """Apply properties to a sprite. Returns applied props."""
        for scene in self._project.scenes:
            for sprite in scene.sprites:
                if sprite.id == target_id or sprite.name == target_id:
                    applied = []
                    if "name" in props:
                        sprite.name = props["name"]
                        applied.append("name")
                    if "x" in props:
                        sprite.x = float(props["x"])
                        applied.append("x")
                    if "y" in props:
                        sprite.y = float(props["y"])
                        applied.append("y")
                    if "size" in props:
                        sprite.size = float(props["size"])
                        applied.append("size")
                    if "direction" in props:
                        sprite.direction = float(props["direction"])
                        applied.append("direction")
                    if "visible" in props:
                        sprite.visible = bool(props["visible"])
                        applied.append("visible")
                    if "is_physics" in props:
                        sprite.is_physics = bool(props["is_physics"])
                        applied.append("is_physics")

                    self._refresh_views()
                    return ", ".join(applied) if applied else ""
        return ""

    def _apply_scene_props(self, target_id: str, props: dict) -> str:
        """Apply properties to a scene. Returns applied props."""
        for scene in self._project.scenes:
            if scene.id == target_id or scene.name == target_id:
                applied = []
                if "name" in props:
                    scene.name = props["name"]
                    applied.append("name")
                if "bg_color" in props:
                    scene.bg_color = props["bg_color"]
                    applied.append("bg_color")
                if "bg_image" in props:
                    scene.bg_image = props["bg_image"]
                    applied.append("bg_image")

                self._refresh_views()
                return ", ".join(applied) if applied else ""
        return ""

    def _apply_game_props(self, props: dict) -> str:
        """Apply properties to game settings. Returns applied props."""
        game = self._project.game
        applied = []
        if "title" in props:
            game.title = props["title"]
            applied.append("title")
        if "width" in props:
            game.width = int(props["width"])
            applied.append("width")
        if "height" in props:
            game.height = int(props["height"])
            applied.append("height")
        if "fps" in props:
            game.fps = int(props["fps"])
            applied.append("fps")
        if "fullscreen" in props:
            game.fullscreen = bool(props["fullscreen"])
            applied.append("fullscreen")
        if "debug" in props:
            game.debug = bool(props["debug"])
            applied.append("debug")

        self._refresh_views()
        return ", ".join(applied) if applied else ""

    def _refresh_views(self):
        """Refresh all views after property changes."""
        if not self._main_window:
            return
        # Mark project as modified
        self._main_window.project.mark_modified()
        # Refresh hierarchy view
        self._main_window.hierarchy_view.refresh()
        # Refresh scene view
        if self._main_window._current_scene:
            self._main_window.scene_view.clear()
            for sprite in self._main_window._current_scene.sprites:
                self._main_window.scene_view.add_sprite(sprite)
        # Refresh property editor
        self._main_window.property_editor.refresh()
        # Update AI context
        self._main_window._build_full_project_context()
