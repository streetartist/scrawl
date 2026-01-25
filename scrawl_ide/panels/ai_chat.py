"""
AI Chat Panel

Chat interface for AI code assistance with code modification support.
"""

import re
import difflib
import json
from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QMessageBox, QComboBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor

import markdown

from core.ai_service import AIService
from core.i18n import tr

if TYPE_CHECKING:
    from models import ProjectModel

from models import SpriteModel, SceneModel


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
        self._ai_message_start_pos = 0  # Track where AI message starts
        self._md = markdown.Markdown(extensions=['fenced_code', 'tables', 'nl2br'])
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Model selector
        model_layout = QHBoxLayout()
        self._model_combo = QComboBox()
        self._model_combo.setStyleSheet("""
            QComboBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #555;
                padding: 4px 8px;
                min-width: 150px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; border: none; }
        """)
        self._setup_model_options()
        self._model_combo.currentIndexChanged.connect(self._on_model_changed)
        model_layout.addWidget(self._model_combo, 1)
        layout.addLayout(model_layout)

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

    def _setup_model_options(self):
        """Setup model dropdown options."""
        # Custom model from settings
        self._model_combo.addItem("⚙️ 自定义 (设置)", "custom")
        # Free models
        for model_id, model_name in AIService.FREE_MODELS:
            self._model_combo.addItem(f"🆓 {model_name}", model_id)
        # Default to first free model
        self._model_combo.setCurrentIndex(1)
        self._on_model_changed(1)

    def _on_model_changed(self, index: int):
        """Handle model selection change."""
        model_data = self._model_combo.currentData()
        if model_data == "custom":
            # Use settings config
            self._ai_service.set_custom_config(None, None, None)
        else:
            # Use free model
            self._ai_service.set_custom_config(
                AIService.FREE_ENDPOINT,
                AIService.FREE_API_KEY,
                model_data
            )

    def _markdown_to_html(self, text: str) -> str:
        """Convert markdown to styled HTML."""
        self._md.reset()
        # Fix unclosed code blocks for streaming
        text = self._fix_unclosed_code_blocks(text)
        html = self._md.convert(text)
        # Wrap in styled container
        styled_html = f'''
        <style>
            pre {{ background-color: #2D2D2D; padding: 10px; border-radius: 4px; overflow-x: auto; }}
            code {{ background-color: #2D2D2D; padding: 2px 4px; border-radius: 3px; font-family: Consolas, monospace; }}
            pre code {{ padding: 0; background: none; }}
            h1, h2, h3, h4 {{ color: #81C784; margin: 8px 0; }}
            ul, ol {{ margin: 8px 0; padding-left: 20px; }}
            li {{ margin: 4px 0; }}
            blockquote {{ border-left: 3px solid #555; padding-left: 10px; margin: 8px 0; color: #AAA; }}
            table {{ border-collapse: collapse; margin: 8px 0; }}
            th, td {{ border: 1px solid #555; padding: 6px 10px; }}
            th {{ background-color: #2D2D2D; }}
        </style>
        {html}
        '''
        return styled_html

    def _fix_unclosed_code_blocks(self, text: str) -> str:
        """Fix unclosed code blocks for proper rendering during streaming."""
        # Convert custom format ```python:sprite:xxx to standard ```python
        text = re.sub(r'```(python|json):(\w+):([^\n]*)', r'```\1', text)

        # Count code block markers
        markers = re.findall(r'```', text)
        if len(markers) % 2 == 1:
            # Odd number of markers, add closing one
            text += '\n```'
        return text

    def _get_current_code(self, target_type: str, target_id: str) -> Optional[str]:
        """Get current code for a target."""
        if not self._project:
            return None
        target_id = target_id.strip()
        if target_type == "sprite":
            for scene in self._project.scenes:
                for sprite in scene.sprites:
                    if sprite.id == target_id or sprite.name == target_id:
                        return sprite.code or ""
        elif target_type == "scene":
            for scene in self._project.scenes:
                if scene.id == target_id or scene.name == target_id:
                    return scene.code or ""
        return None

    def _generate_diff_html(self, old_code: str, new_code: str, max_lines: int = 20) -> str:
        """Generate HTML diff view like Claude Code."""
        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)

        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))

        # unified_diff returns: ['--- ...', '+++ ...', '@@ ... @@', ...actual diff...]
        # If empty or only headers, no real changes
        if not diff or len(diff) <= 2:
            return '<p style="color: #888;">无变化</p>'

        html_parts = []
        line_count = 0

        for line in diff[2:]:  # Skip --- and +++ headers
            if line_count >= max_lines:
                html_parts.append('<p style="color: #888;">... 更多变化已省略</p>')
                break

            line_escaped = line.rstrip('\n').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            if line.startswith('+'):
                html_parts.append(f'<div style="background:#1e3a1e;color:#4ade80;padding:1px 8px;font-family:Consolas,monospace;font-size:11pt;">{line_escaped}</div>')
                line_count += 1
            elif line.startswith('-'):
                html_parts.append(f'<div style="background:#3a1e1e;color:#f87171;padding:1px 8px;font-family:Consolas,monospace;font-size:11pt;">{line_escaped}</div>')
                line_count += 1
            elif line.startswith('@@'):
                html_parts.append(f'<div style="color:#60a5fa;padding:2px 8px;font-size:10pt;">{line_escaped}</div>')

        return ''.join(html_parts)

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
        """Handle response chunk with real-time markdown rendering."""
        self._current_response += chunk

        if not self._streaming_started:
            # Add newline before AI message
            self._chat_display.append("")
            # Record position before AI message
            cursor = self._chat_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            self._ai_message_start_pos = cursor.position()
            self._streaming_started = True

        # Delete previous AI response content and re-render
        cursor = self._chat_display.textCursor()
        cursor.setPosition(self._ai_message_start_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()

        # Render markdown and insert
        rendered_html = self._markdown_to_html(self._current_response)
        ai_html = f'<p style="color: #81C784;"><b>AI:</b></p>{rendered_html}'
        cursor.insertHtml(ai_html)

        self._scroll_to_bottom()

    def _on_response_done(self):
        """Handle response completion."""
        self._ai_service.add_assistant_message(self._current_response)
        self._send_btn.setEnabled(True)
        # Add spacing after response
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
        """Show preview of pending changes with diff view like Claude Code."""
        html_parts = []

        # Check code blocks
        code_blocks = self._extract_code_blocks()
        for target_type, target_id, new_code in code_blocks:
            if not target_type or not target_id:
                continue
            target_id = target_id.strip()
            new_code = new_code.strip()

            # Build header
            header = f'''
            <div style="background:#2D2D2D;border:1px solid #555;border-radius:6px;margin:8px 0;overflow:hidden;">
                <div style="background:#3D3D3D;padding:8px 12px;border-bottom:1px solid #555;">
                    <span style="color:#FFA726;font-weight:bold;">📝 代码修改</span>
                    <span style="color:#81C784;margin-left:10px;">{target_type}:{target_id}</span>
                </div>
            '''

            # Get current code and generate diff
            current_code = self._get_current_code(target_type, target_id)
            if current_code is not None:
                diff_html = self._generate_diff_html(current_code, new_code)
                html_parts.append(f'{header}<div style="padding:4px 0;">{diff_html}</div></div>')
            else:
                # New code, show as all additions
                escaped = new_code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                lines = escaped.split('\n')
                new_html = ''.join(
                    f'<div style="background:#1e3a1e;color:#4ade80;padding:1px 8px;font-family:Consolas,monospace;font-size:11pt;">+{line}</div>'
                    for line in lines[:20]
                )
                if len(lines) > 20:
                    new_html += '<p style="color:#888;padding:4px 8px;">... 更多行已省略</p>'
                html_parts.append(f'{header}<div style="padding:4px 0;">{new_html}</div></div>')

        # Check property blocks
        json_blocks = self._extract_json_blocks()
        for target_type, target_id, json_str in json_blocks:
            if not target_type or not target_id:
                continue
            target_id = target_id.strip()
            try:
                props = json.loads(json_str.strip())
                props_html = ''.join(
                    f'<div style="padding:2px 12px;"><span style="color:#60a5fa;">{k}</span>: <span style="color:#4ade80;">{v}</span></div>'
                    for k, v in props.items()
                )
                html_parts.append(f'''
                <div style="background:#2D2D2D;border:1px solid #555;border-radius:6px;margin:8px 0;overflow:hidden;">
                    <div style="background:#3D3D3D;padding:8px 12px;border-bottom:1px solid #555;">
                        <span style="color:#FFA726;font-weight:bold;">⚙️ 属性修改</span>
                        <span style="color:#81C784;margin-left:10px;">{target_type}:{target_id}</span>
                    </div>
                    <div style="padding:8px 0;font-family:Consolas,monospace;font-size:11pt;">{props_html}</div>
                </div>
                ''')
            except json.JSONDecodeError:
                pass

        if html_parts:
            self._chat_display.append(''.join(html_parts))
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
        """Apply code to a sprite by id or name. Creates sprite if not found."""
        # First try to find existing sprite
        for scene in self._project.scenes:
            for sprite in scene.sprites:
                if sprite.id == target_id or sprite.name == target_id:
                    sprite.code = code
                    self._update_editor(f"sprite:{sprite.id}", code)
                    if self._main_window:
                        self._main_window.project.mark_modified()
                    return True

        # Sprite not found, create new one in current scene
        if self._main_window and self._main_window._current_scene:
            sprite = SpriteModel.create_default(target_id)
            sprite.code = code
            self._main_window._current_scene.sprites.append(sprite)
            self._main_window.scene_view.add_sprite(sprite)
            self._main_window.hierarchy_view.refresh()
            self._main_window.project.mark_modified()
            return True
        return False

    def _apply_to_scene(self, target_id: str, code: str) -> bool:
        """Apply code to a scene by id or name. Creates scene if not found."""
        # First try to find existing scene
        for scene in self._project.scenes:
            if scene.id == target_id or scene.name == target_id:
                scene.code = code
                self._update_editor(f"scene:{scene.id}", code)
                if self._main_window:
                    self._main_window.project.mark_modified()
                return True

        # Scene not found, create new one
        if self._main_window:
            scene = SceneModel.create_default(target_id)
            scene.code = code
            self._project.scenes.append(scene)
            self._main_window.hierarchy_view.refresh()
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
        """Apply properties to a sprite. Creates sprite if not found."""
        sprite = None
        target_scene = None

        # Find existing sprite
        for scene in self._project.scenes:
            for s in scene.sprites:
                if s.id == target_id or s.name == target_id:
                    sprite = s
                    target_scene = scene
                    break
            if sprite:
                break

        # Create new sprite if not found
        if not sprite and self._main_window and self._main_window._current_scene:
            sprite = SpriteModel.create_default(target_id)
            self._main_window._current_scene.sprites.append(sprite)
            self._main_window.scene_view.add_sprite(sprite)
            target_scene = self._main_window._current_scene

        if not sprite:
            return ""

        # Apply properties
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

        # Handle code-drawn costumes
        if "add_code_costume" in props:
            costume_data = props["add_code_costume"]
            if isinstance(costume_data, dict):
                name = costume_data.get("name", "costume")
                width = int(costume_data.get("width", 32))
                height = int(costume_data.get("height", 32))
                draw_code = costume_data.get("draw_code", "")
                if draw_code:
                    idx = sprite.add_code_costume(name, width, height, draw_code)
                    sprite.current_costume = idx # Switch to new costume
                    applied.append(f"costume:{name}")

        self._refresh_views()
        return ", ".join(applied) if applied else ""

    def _apply_scene_props(self, target_id: str, props: dict) -> str:
        """Apply properties to a scene. Creates scene if not found."""
        scene = None

        # Find existing scene
        for s in self._project.scenes:
            if s.id == target_id or s.name == target_id:
                scene = s
                break

        # Create new scene if not found
        if not scene and self._main_window:
            scene = SceneModel.create_default(target_id)
            self._project.scenes.append(scene)

        if not scene:
            return ""

        # Apply properties
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
