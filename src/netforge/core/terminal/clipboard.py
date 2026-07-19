"""
OS clipboard integration for the terminal widget.
"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

# Bracketed paste mode markers (xterm extension). Wrapping pasted text
# in these lets shell readlines (bash, zsh, etc.) tell the difference
# between typed input and a paste, which prevents auto-indent/history
# expansion mangling multi-line pastes.
_BRACKETED_PASTE_START = b"\x1b[200~"
_BRACKETED_PASTE_END = b"\x1b[201~"


class ClipboardManager:
    """Thin wrapper around the system clipboard for the terminal widget."""

    def copy(self, text: str) -> None:
        """Copy plain text to the system clipboard."""
        if not text:
            return

        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)

    def paste_text(self) -> str:
        """Read plain text currently on the system clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return ""
        return clipboard.text()

    def paste_bytes(self, bracketed: bool = True) -> bytes:
        """
        Read the clipboard and encode it for sending to the remote
        PTY, optionally wrapped in bracketed-paste markers.
        """
        text = self.paste_text()
        if not text:
            return b""

        data = text.replace("\r\n", "\n").replace("\n", "\r").encode(
            "utf-8", errors="replace"
        )

        if bracketed:
            return _BRACKETED_PASTE_START + data + _BRACKETED_PASTE_END

        return data
