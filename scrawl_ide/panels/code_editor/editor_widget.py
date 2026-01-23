"""
Code Editor Widget

Python code editor with syntax highlighting using PySide6.
"""

import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QMessageBox,
    QMenu, QToolBar, QToolButton
)
from PySide6.QtCore import Signal, Qt, QRect, QSize
from PySide6.QtGui import (
    QFont, QColor, QPainter, QTextFormat, QSyntaxHighlighter,
    QTextCharFormat, QFontMetrics, QTextCursor, QTextDocument
)

from core.settings import Settings
from .snippets import (
    DECORATOR_SNIPPETS, FUNCTION_SNIPPETS,
    get_decorator_categories, get_function_categories,
    get_decorators_by_category, get_functions_by_category
)


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Define formats
        self._formats = {}

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Bold)
        self._formats['keyword'] = keyword_format

        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#DCDCAA"))
        self._formats['decorator'] = decorator_format

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        self._formats['string'] = string_format

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)
        self._formats['comment'] = comment_format

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self._formats['number'] = number_format

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))
        self._formats['function'] = function_format

        # Class names
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4EC9B0"))
        self._formats['class'] = class_format

        # Self
        self_format = QTextCharFormat()
        self_format.setForeground(QColor("#9CDCFE"))
        self._formats['self'] = self_format

        # Python keywords
        self._keywords = [
            'and', 'as', 'assert', 'async', 'await', 'break', 'class',
            'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
            'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
            'while', 'with', 'yield', 'True', 'False', 'None'
        ]

    def highlightBlock(self, text: str):
        """Highlight a block of text."""
        # Comments
        comment_start = text.find('#')
        if comment_start >= 0:
            # Check if # is inside a string
            in_string = False
            for i, char in enumerate(text[:comment_start]):
                if char in '"\'':
                    in_string = not in_string
            if not in_string:
                self.setFormat(comment_start, len(text) - comment_start, self._formats['comment'])
                text = text[:comment_start]  # Don't process rest

        # Decorators
        stripped = text.lstrip()
        if stripped.startswith('@'):
            indent = len(text) - len(stripped)
            end = len(text)
            for i, c in enumerate(stripped[1:], 1):
                if not (c.isalnum() or c == '_'):
                    end = indent + i
                    break
            self.setFormat(indent, end - indent, self._formats['decorator'])

        # Strings (simple handling)
        self._highlight_strings(text)

        # Keywords
        import re
        for keyword in self._keywords:
            pattern = rf'\b{keyword}\b'
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), self._formats['keyword'])

        # self
        for match in re.finditer(r'\bself\b', text):
            self.setFormat(match.start(), 4, self._formats['self'])

        # Numbers
        for match in re.finditer(r'\b\d+\.?\d*\b', text):
            self.setFormat(match.start(), match.end() - match.start(), self._formats['number'])

        # Function definitions
        for match in re.finditer(r'\bdef\s+(\w+)', text):
            self.setFormat(match.start(1), match.end(1) - match.start(1), self._formats['function'])

        # Class definitions
        for match in re.finditer(r'\bclass\s+(\w+)', text):
            self.setFormat(match.start(1), match.end(1) - match.start(1), self._formats['class'])

    def _highlight_strings(self, text: str):
        """Highlight string literals."""
        import re

        # Triple quotes
        for match in re.finditer(r'""".*?"""|\'\'\'.*?\'\'\'', text):
            self.setFormat(match.start(), match.end() - match.start(), self._formats['string'])

        # Single and double quotes (simple)
        for match in re.finditer(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'', text):
            self.setFormat(match.start(), match.end() - match.start(), self._formats['string'])


class LineNumberArea(QWidget):
    """Line number area for the code editor."""

    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Code editor with line numbers and syntax highlighting."""

    # Font size limits
    MIN_FONT_SIZE = 8
    MAX_FONT_SIZE = 32

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settings = Settings()
        self._font_family = self._settings.get_font_family()
        self._font_size = self._settings.get_font_size()

        # Setup font and colors via stylesheet
        self._apply_font_stylesheet()

        # Line number area
        self._line_number_area = LineNumberArea(self)

        # Connect signals
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        # Initial setup
        self._update_line_number_area_width(0)
        self._highlight_current_line()

        # Syntax highlighter
        self._highlighter = PythonHighlighter(self.document())

        # Tab settings - use fontMetrics() after stylesheet is applied
        tab_width = self._settings.get_tab_width()
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * tab_width)

    def _apply_font_stylesheet(self):
        """Apply font settings via stylesheet."""
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #1E1E1E;
                color: #E0E0E0;
                selection-background-color: #264F78;
                selection-color: #FFFFFF;
                border: none;
                font-family: "{self._font_family}";
                font-size: {self._font_size}pt;
            }}
        """)

    def set_font_size(self, size: int):
        """Set font size and update display."""
        self._font_size = max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, size))
        self._apply_font_stylesheet()
        self._update_line_number_area_width(0)

    def wheelEvent(self, event):
        """Handle mouse wheel - Ctrl+wheel to zoom."""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.set_font_size(self._font_size + 1)
            elif delta < 0:
                self.set_font_size(self._font_size - 1)
            event.accept()
        else:
            super().wheelEvent(event)

    def line_number_area_width(self) -> int:
        """Calculate the width needed for line numbers."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def _update_line_number_area_width(self, _):
        """Update the margin for line numbers."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        """Update the line number area on scroll."""
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Handle resize."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def _highlight_current_line(self):
        """Highlight the current line by triggering a repaint."""
        # Simply update the viewport to trigger paintEvent
        self.viewport().update()

    def paintEvent(self, event):
        """Override paint to draw current line highlight."""
        # Draw current line highlight first
        if not self.isReadOnly():
            painter = QPainter(self.viewport())
            cursor = self.textCursor()
            block = cursor.block()
            if block.isValid():
                rect = self.blockBoundingGeometry(block).translated(self.contentOffset())
                painter.fillRect(
                    0, int(rect.top()),
                    self.viewport().width(), int(rect.height()),
                    QColor("#282828")
                )
            painter.end()

        # Call parent paintEvent
        super().paintEvent(event)

    def line_number_area_paint_event(self, event):
        """Paint line numbers."""
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#1E1E1E"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(
                    0, top,
                    self._line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def keyPressEvent(self, event):
        """Handle key press for auto-indent."""
        # Dedent keywords
        dedent_keywords = ('return', 'break', 'continue', 'pass', 'raise')

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_enter_key()
        elif event.key() == Qt.Key_Tab:
            if event.modifiers() & Qt.ShiftModifier:
                self._handle_dedent()
            else:
                self._handle_indent()
        elif event.key() == Qt.Key_Backtab:
            self._handle_dedent()
        elif event.key() == Qt.Key_Backspace:
            if not self._handle_smart_backspace():
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
            # Auto-dedent after typing dedent keywords
            if event.text() and event.text().isalpha():
                self._check_auto_dedent(dedent_keywords)

    def _get_line_indent(self, line: str) -> str:
        """Get the indentation of a line."""
        indent = ""
        for char in line:
            if char in ' \t':
                indent += char
            else:
                break
        return indent

    def _handle_enter_key(self):
        """Handle Enter key with smart indentation."""
        cursor = self.textCursor()
        line = cursor.block().text()
        indent = self._get_line_indent(line)
        line_stripped = line.strip()

        # Increase indent after colon
        if line_stripped.endswith(':'):
            indent += "    "
        # Decrease indent after dedent keywords
        elif line_stripped in ('return', 'break', 'continue', 'pass') or \
             line_stripped.startswith(('return ', 'raise ')):
            if len(indent) >= 4:
                indent = indent[:-4]

        # Check for unclosed brackets
        text_before = line[:cursor.positionInBlock()]
        open_brackets = text_before.count('(') - text_before.count(')')
        open_brackets += text_before.count('[') - text_before.count(']')
        open_brackets += text_before.count('{') - text_before.count('}')
        if open_brackets > 0:
            indent += "    "

        # Insert newline and indent
        cursor.insertText('\n' + indent)
        self.setTextCursor(cursor)

    def _handle_indent(self):
        """Handle Tab key - indent current line or selection."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            # Indent all selected lines
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)

            text = cursor.selectedText()
            # QTextCursor uses \u2029 as paragraph separator
            lines = text.split('\u2029')
            indented = ['    ' + line for line in lines]
            cursor.insertText('\u2029'.join(indented))
        else:
            # Insert 4 spaces at cursor
            cursor.insertText("    ")

    def _handle_dedent(self):
        """Handle Shift+Tab - dedent current line or selection."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            # Dedent all selected lines
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)

            text = cursor.selectedText()
            lines = text.split('\u2029')
            dedented = []
            for line in lines:
                if line.startswith('    '):
                    dedented.append(line[4:])
                elif line.startswith('\t'):
                    dedented.append(line[1:])
                else:
                    dedented.append(line.lstrip(' \t') if line.startswith((' ', '\t')) else line)
            cursor.insertText('\u2029'.join(dedented))
        else:
            # Dedent current line
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            line = cursor.selectedText()
            if line.startswith('    '):
                cursor.insertText(line[4:])
            elif line.startswith('\t'):
                cursor.insertText(line[1:])

    def _handle_smart_backspace(self) -> bool:
        """Handle Backspace with smart indent deletion. Returns True if handled."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False

        # Check if cursor is at the start of indentation
        pos_in_block = cursor.positionInBlock()
        line = cursor.block().text()

        # If we're in the indentation area and it's all spaces
        if pos_in_block > 0 and line[:pos_in_block].strip() == '':
            # Delete up to 4 spaces backwards
            spaces_before = pos_in_block
            delete_count = min(4, spaces_before)
            # Align to 4-space boundary
            delete_count = spaces_before % 4 or 4
            for _ in range(delete_count):
                cursor.deletePreviousChar()
            return True
        return False

    def _check_auto_dedent(self, dedent_keywords):
        """Check if current line should be auto-dedented after typing a keyword."""
        cursor = self.textCursor()
        line = cursor.block().text()
        stripped = line.strip()

        # Check if line is exactly a dedent keyword
        if stripped in dedent_keywords:
            indent = self._get_line_indent(line)
            if len(indent) >= 4:
                # Already at correct indent, no change needed
                pass

    def contextMenuEvent(self, event):
        """Show context menu with snippet insertion options."""
        menu = self.createStandardContextMenu()
        menu.addSeparator()

        # Insert Decorator submenu
        decorator_menu = menu.addMenu("插入装饰器")
        for category in get_decorator_categories():
            cat_menu = decorator_menu.addMenu(category)
            for snippet in get_decorators_by_category(category):
                action = cat_menu.addAction(snippet["name"])
                action.setToolTip(snippet["description"])
                action.triggered.connect(
                    lambda checked, s=snippet: self._insert_snippet(s["template"])
                )

        # Insert Function submenu
        function_menu = menu.addMenu("插入函数")
        for category in get_function_categories():
            cat_menu = function_menu.addMenu(category)
            for snippet in get_functions_by_category(category):
                action = cat_menu.addAction(snippet["name"])
                action.setToolTip(snippet["description"])
                action.triggered.connect(
                    lambda checked, s=snippet: self._insert_snippet(s["template"])
                )

        menu.exec_(event.globalPos())

    def _insert_snippet(self, template: str):
        """Insert a code snippet at the current cursor position."""
        cursor = self.textCursor()

        # Get current line indentation
        current_line = cursor.block().text()
        indent = ""
        for char in current_line:
            if char in ' \t':
                indent += char
            else:
                break

        # Adjust template indentation
        lines = template.split('\n')
        adjusted_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                adjusted_lines.append(line)
            elif line.strip():
                adjusted_lines.append(indent + line)
            else:
                adjusted_lines.append(line)

        adjusted_template = '\n'.join(adjusted_lines)

        # Insert at cursor
        cursor.insertText(adjusted_template)
        self.setTextCursor(cursor)
        self.setFocus()


class CodeEditorWidget(QWidget):
    """Code editor widget with syntax highlighting."""

    text_changed = Signal()
    file_saved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._file_path: Optional[str] = None
        self._modified = False
        self._settings = Settings()

        self._setup_ui()

    @property
    def file_path(self) -> Optional[str]:
        return self._file_path

    @property
    def is_modified(self) -> bool:
        return self._modified

    def _setup_ui(self):
        """Set up the editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar for insert buttons
        self._toolbar = QToolBar()
        self._toolbar.setMovable(False)
        self._toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2D2D2D;
                border: none;
                padding: 2px;
                spacing: 4px;
            }
            QToolButton {
                background-color: #3C3C3C;
                color: #E0E0E0;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QToolButton:hover {
                background-color: #4A4A4A;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        self._setup_toolbar()
        layout.addWidget(self._toolbar)

        # Code editor
        self._editor = CodeEditor(self)
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

    def _setup_toolbar(self):
        """Set up the insert toolbar."""
        # Insert Decorator button
        decorator_btn = QToolButton()
        decorator_btn.setText("插入装饰器 ▼")
        decorator_btn.setPopupMode(QToolButton.InstantPopup)
        decorator_menu = self._create_decorator_menu()
        decorator_btn.setMenu(decorator_menu)
        self._toolbar.addWidget(decorator_btn)

        # Insert Function button
        function_btn = QToolButton()
        function_btn.setText("插入函数 ▼")
        function_btn.setPopupMode(QToolButton.InstantPopup)
        function_menu = self._create_function_menu()
        function_btn.setMenu(function_menu)
        self._toolbar.addWidget(function_btn)

    def _create_decorator_menu(self) -> QMenu:
        """Create the decorator insertion menu."""
        menu = QMenu(self)
        for category in get_decorator_categories():
            cat_menu = menu.addMenu(category)
            for snippet in get_decorators_by_category(category):
                action = cat_menu.addAction(snippet["name"])
                action.setToolTip(snippet["description"])
                action.triggered.connect(
                    lambda checked, s=snippet: self._insert_snippet(s["template"])
                )
        return menu

    def _create_function_menu(self) -> QMenu:
        """Create the function insertion menu."""
        menu = QMenu(self)
        for category in get_function_categories():
            cat_menu = menu.addMenu(category)
            for snippet in get_functions_by_category(category):
                action = cat_menu.addAction(snippet["name"])
                action.setToolTip(snippet["description"])
                action.triggered.connect(
                    lambda checked, s=snippet: self._insert_snippet(s["template"])
                )
        return menu

    def _insert_snippet(self, template: str):
        """Insert a code snippet at the current cursor position."""
        self._editor._insert_snippet(template)

    def _on_text_changed(self):
        """Handle text changes."""
        if not self._modified:
            self._modified = True
        self.text_changed.emit()

    def open_file(self, path: str) -> bool:
        """Open a file in the editor."""
        if not os.path.exists(path):
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            self._editor.setPlainText(content)
            self._file_path = path
            self._modified = False
            return True

        except IOError as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {e}")
            return False

    def save_file(self, path: Optional[str] = None) -> bool:
        """Save the editor content to a file."""
        save_path = path or self._file_path

        if not save_path:
            return False

        try:
            content = self._editor.toPlainText()

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self._file_path = save_path
            self._modified = False
            self.file_saved.emit(save_path)
            return True

        except IOError as e:
            QMessageBox.warning(self, "Error", f"Could not save file: {e}")
            return False

    def get_text(self) -> str:
        """Get the editor text content."""
        return self._editor.toPlainText()

    def set_text(self, text: str):
        """Set the editor text content."""
        self._editor.setPlainText(text)
        self._modified = False

    def clear(self):
        """Clear the editor."""
        self._editor.clear()
        self._file_path = None
        self._modified = False

    def goto_line(self, line: int):
        """Go to a specific line."""
        cursor = self._editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for _ in range(line - 1):
            cursor.movePosition(QTextCursor.Down)
        self._editor.setTextCursor(cursor)
        self._editor.centerCursor()

    def find_text(self, text: str, case_sensitive: bool = False,
                  whole_word: bool = False, regex: bool = False) -> bool:
        """Find text in the editor."""
        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords

        return self._editor.find(text, flags)

    def replace_text(self, find: str, replace: str,
                     case_sensitive: bool = False) -> int:
        """Replace all occurrences of text."""
        content = self._editor.toPlainText()
        if case_sensitive:
            new_content = content.replace(find, replace)
        else:
            import re
            new_content = re.sub(re.escape(find), replace, content, flags=re.IGNORECASE)

        if new_content != content:
            count = content.count(find) if case_sensitive else len(re.findall(re.escape(find), content, re.IGNORECASE))
            self._editor.setPlainText(new_content)
            return count
        return 0
