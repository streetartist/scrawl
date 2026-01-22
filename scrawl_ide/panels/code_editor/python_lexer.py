"""
Python Lexer Configuration

Configuration for Python syntax highlighting in QScintilla.
"""

from PyQt5.Qsci import QsciLexerPython
from PySide6.QtGui import QColor, QFont


class PythonLexerConfig:
    """Configuration helper for Python lexer in QScintilla."""

    # Style indices for Python lexer
    DEFAULT = 0
    COMMENT = 1
    NUMBER = 2
    DOUBLE_QUOTED_STRING = 3
    SINGLE_QUOTED_STRING = 4
    KEYWORD = 5
    TRIPLE_SINGLE_QUOTED_STRING = 6
    TRIPLE_DOUBLE_QUOTED_STRING = 7
    CLASS_NAME = 8
    FUNCTION_METHOD_NAME = 9
    OPERATOR = 10
    IDENTIFIER = 11
    COMMENT_BLOCK = 12
    UNCLOSED_STRING = 13
    HIGHLIGHTED_IDENTIFIER = 14
    DECORATOR = 15

    # Dark theme colors
    DARK_THEME = {
        DEFAULT: ("#D4D4D4", None),  # Default text
        COMMENT: ("#6A9955", None),  # Green comments
        NUMBER: ("#B5CEA8", None),  # Light green numbers
        DOUBLE_QUOTED_STRING: ("#CE9178", None),  # Orange strings
        SINGLE_QUOTED_STRING: ("#CE9178", None),
        KEYWORD: ("#569CD6", None),  # Blue keywords
        TRIPLE_SINGLE_QUOTED_STRING: ("#CE9178", None),
        TRIPLE_DOUBLE_QUOTED_STRING: ("#CE9178", None),
        CLASS_NAME: ("#4EC9B0", None),  # Teal class names
        FUNCTION_METHOD_NAME: ("#DCDCAA", None),  # Yellow functions
        OPERATOR: ("#D4D4D4", None),
        IDENTIFIER: ("#9CDCFE", None),  # Light blue identifiers
        COMMENT_BLOCK: ("#6A9955", None),
        UNCLOSED_STRING: ("#CE9178", "#FF0000"),  # Red background for unclosed
        HIGHLIGHTED_IDENTIFIER: ("#4FC1FF", None),
        DECORATOR: ("#DCDCAA", None),  # Yellow decorators
    }

    # Python keywords to highlight
    KEYWORDS = (
        "False None True and as assert async await break class continue "
        "def del elif else except finally for from global if import in is "
        "lambda nonlocal not or pass raise return try while with yield "
        "self cls"
    )

    @classmethod
    def apply_dark_theme(cls, lexer):
        """Apply dark theme colors to a Python lexer."""
        for style, (fg, bg) in cls.DARK_THEME.items():
            if fg:
                lexer.setColor(QColor(fg), style)
            if bg:
                lexer.setPaper(QColor(bg), style)

    @classmethod
    def configure_lexer(cls, lexer, font_family: str = "Consolas", font_size: int = 11):
        """Configure a Python lexer with default settings."""
        # Set font
        font = QFont(font_family, font_size)
        lexer.setFont(font)

        # Set keywords
        lexer.setKeywords(0, cls.KEYWORDS)

        # Apply dark theme
        cls.apply_dark_theme(lexer)

        return lexer
