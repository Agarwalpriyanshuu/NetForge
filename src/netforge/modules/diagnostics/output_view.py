"""
Shared read-only, monospace output view used by every diagnostic
tool panel (Ping, Traceroute, DNS Lookup, Port Scanner), so streamed
results all look and behave consistently.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

_COLORS = {
    "normal": None,  # inherit the theme's default text color
    "success": "#23d18b",
    "error": "#f14c4c",
    "muted": "#9d9d9d",
    "info": "#3b8eea",
}


class DiagnosticOutput(QPlainTextEdit):
    """A styled, append-only output console for diagnostic tool results."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)

    def append_line(self, text: str, style: str = "normal") -> None:
        color = _COLORS.get(style)

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        char_format = cursor.charFormat()
        if color:
            char_format.setForeground(QColor(color))
        else:
            char_format.clearForeground()

        cursor.setCharFormat(char_format)
        cursor.insertText(text + "\n")

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear_output(self) -> None:
        self.clear()
