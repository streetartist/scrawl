"""
Code Editor Widget

QScintilla-based code editor with Python syntax highlighting.
"""

import os
from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont, QColor

# Try to import QScintilla - it may not be installed
# Try multiple import paths for compatibility
QSCINTILLA_AVAILABLE = False
QsciScintilla = None
QsciLexerPython = None

try:
    # Try PySide6 version first
    from PySide6.Qsci import QsciScintilla, QsciLexerPython
    QSCINTILLA_AVAILABLE = True
except ImportError:
    try:
        # Try PyQt6 version
        from PyQt6.Qsci import QsciScintilla, QsciLexerPython
        QSCINTILLA_AVAILABLE = True
    except ImportError:
        try:
            # Try PyQt5 version as fallback
            from PyQt5.Qsci import QsciScintilla, QsciLexerPython
            QSCINTILLA_AVAILABLE = True
        except ImportError:
            pass

from core.settings import Settings


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

        if QSCINTILLA_AVAILABLE:
            self._editor = QsciScintilla(self)
            self._setup_editor()
        else:
            # Fallback to plain text edit
            from PySide6.QtWidgets import QPlainTextEdit
            self._editor = QPlainTextEdit(self)
            editor_font = QFont(
                self._settings.get_font_family(),
                self._settings.get_font_size()
            )
            self._editor.setFont(editor_font)
            # Apply dark theme styling
            self._editor.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #1E1E1E;
                    color: #E0E0E0;
                    selection-background-color: #264F78;
                    selection-color: #FFFFFF;
                    border: none;
                }
            """)
            self._editor.textChanged.connect(self._on_text_changed)

        layout.addWidget(self._editor)

    def _setup_editor(self):
        """Configure the QScintilla editor."""
        editor = self._editor

        # Font
        font_family = self._settings.get_font_family()
        font_size = self._settings.get_font_size()
        font = QFont(font_family, font_size)
        editor.setFont(font)

        # Margins
        editor.setMarginType(0, QsciScintilla.NumberMargin)
        editor.setMarginWidth(0, "00000")
        editor.setMarginsForegroundColor(QColor("#858585"))
        editor.setMarginsBackgroundColor(QColor("#1E1E1E"))
        editor.setMarginLineNumbers(0, True)

        # Folding
        editor.setFolding(QsciScintilla.BoxedTreeFoldStyle)
        editor.setFoldMarginColors(QColor("#1E1E1E"), QColor("#1E1E1E"))

        # Indentation
        tab_width = self._settings.get_tab_width()
        use_spaces = self._settings.get_use_spaces()
        editor.setIndentationsUseTabs(not use_spaces)
        editor.setTabWidth(tab_width)
        editor.setAutoIndent(True)
        editor.setIndentationGuides(True)
        editor.setIndentationGuidesBackgroundColor(QColor("#404040"))
        editor.setIndentationGuidesForegroundColor(QColor("#404040"))

        # Brace matching
        editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        editor.setMatchedBraceBackgroundColor(QColor("#3A3D41"))
        editor.setMatchedBraceForegroundColor(QColor("#FFFF00"))

        # Caret
        editor.setCaretForegroundColor(QColor("#AEAFAD"))
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor("#282828"))
        editor.setCaretWidth(2)

        # Selection
        editor.setSelectionBackgroundColor(QColor("#264F78"))

        # Edge mode (right margin)
        editor.setEdgeMode(QsciScintilla.EdgeLine)
        editor.setEdgeColumn(100)
        editor.setEdgeColor(QColor("#404040"))

        # Background
        editor.setPaper(QColor("#1E1E1E"))

        # Whitespace
        editor.setWhitespaceVisibility(QsciScintilla.WsInvisible)

        # Auto-completion
        editor.setAutoCompletionSource(QsciScintilla.AcsAll)
        editor.setAutoCompletionThreshold(2)
        editor.setAutoCompletionCaseSensitivity(False)
        editor.setAutoCompletionReplaceWord(True)

        # Lexer for Python
        lexer = QsciLexerPython(editor)
        lexer.setDefaultFont(font)

        # Configure lexer colors (dark theme)
        lexer.setDefaultPaper(QColor("#1E1E1E"))
        lexer.setPaper(QColor("#1E1E1E"))
        lexer.setColor(QColor("#E0E0E0"))  # Default

        # Comments
        lexer.setColor(QColor("#6A9955"), QsciLexerPython.Comment)
        lexer.setColor(QColor("#6A9955"), QsciLexerPython.CommentBlock)

        # Strings
        lexer.setColor(QColor("#CE9178"), QsciLexerPython.DoubleQuotedString)
        lexer.setColor(QColor("#CE9178"), QsciLexerPython.SingleQuotedString)
        lexer.setColor(QColor("#CE9178"), QsciLexerPython.TripleDoubleQuotedString)
        lexer.setColor(QColor("#CE9178"), QsciLexerPython.TripleSingleQuotedString)

        # Keywords
        lexer.setColor(QColor("#569CD6"), QsciLexerPython.Keyword)

        # Numbers
        lexer.setColor(QColor("#B5CEA8"), QsciLexerPython.Number)

        # Functions and classes
        lexer.setColor(QColor("#DCDCAA"), QsciLexerPython.FunctionMethodName)
        lexer.setColor(QColor("#4EC9B0"), QsciLexerPython.ClassName)

        # Decorators
        lexer.setColor(QColor("#DCDCAA"), QsciLexerPython.Decorator)

        # Identifiers
        lexer.setColor(QColor("#9CDCFE"), QsciLexerPython.Identifier)

        # Operators
        lexer.setColor(QColor("#E0E0E0"), QsciLexerPython.Operator)

        editor.setLexer(lexer)

        # Connect signals
        editor.textChanged.connect(self._on_text_changed)

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

            if QSCINTILLA_AVAILABLE:
                self._editor.setText(content)
            else:
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
            if QSCINTILLA_AVAILABLE:
                content = self._editor.text()
            else:
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
        if QSCINTILLA_AVAILABLE:
            return self._editor.text()
        else:
            return self._editor.toPlainText()

    def set_text(self, text: str):
        """Set the editor text content."""
        if QSCINTILLA_AVAILABLE:
            self._editor.setText(text)
        else:
            self._editor.setPlainText(text)
        self._modified = False

    def clear(self):
        """Clear the editor."""
        if QSCINTILLA_AVAILABLE:
            self._editor.clear()
        else:
            self._editor.clear()
        self._file_path = None
        self._modified = False

    def goto_line(self, line: int):
        """Go to a specific line."""
        if QSCINTILLA_AVAILABLE:
            self._editor.setCursorPosition(line - 1, 0)
            self._editor.ensureLineVisible(line - 1)

    def find_text(self, text: str, case_sensitive: bool = False,
                  whole_word: bool = False, regex: bool = False) -> bool:
        """Find text in the editor."""
        if QSCINTILLA_AVAILABLE:
            return self._editor.findFirst(
                text, regex, case_sensitive, whole_word,
                True, True
            )
        return False

    def replace_text(self, find: str, replace: str,
                     case_sensitive: bool = False) -> int:
        """Replace all occurrences of text."""
        if not QSCINTILLA_AVAILABLE:
            return 0

        count = 0
        if self._editor.findFirst(find, False, case_sensitive, False, True, True):
            self._editor.replace(replace)
            count = 1
            while self._editor.findNext():
                self._editor.replace(replace)
                count += 1
        return count
