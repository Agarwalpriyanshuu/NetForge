"""
Translates Qt key events into the raw byte sequences a terminal
expects to receive over the wire (VT100/xterm control codes).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

# Arrow/navigation keys in "normal" cursor key mode (the common case).
_NORMAL_MODE_SEQUENCES = {
    Qt.Key.Key_Up: b"\x1b[A",
    Qt.Key.Key_Down: b"\x1b[B",
    Qt.Key.Key_Right: b"\x1b[C",
    Qt.Key.Key_Left: b"\x1b[D",
}

# The same keys in "application" cursor key mode (DECCKM, used by
# full-screen apps like vim/htop). NetForge does not currently track
# DECCKM mode changes from the remote, so this is exposed for future
# use but normal mode is used by default, which is compatible with
# the vast majority of shells and tools.
_APPLICATION_MODE_SEQUENCES = {
    Qt.Key.Key_Up: b"\x1bOA",
    Qt.Key.Key_Down: b"\x1bOB",
    Qt.Key.Key_Right: b"\x1bOC",
    Qt.Key.Key_Left: b"\x1bOD",
}

_NAVIGATION_SEQUENCES = {
    Qt.Key.Key_Home: b"\x1b[H",
    Qt.Key.Key_End: b"\x1b[F",
    Qt.Key.Key_PageUp: b"\x1b[5~",
    Qt.Key.Key_PageDown: b"\x1b[6~",
    Qt.Key.Key_Insert: b"\x1b[2~",
    Qt.Key.Key_Delete: b"\x1b[3~",
}

_FUNCTION_SEQUENCES = {
    Qt.Key.Key_F1: b"\x1bOP",
    Qt.Key.Key_F2: b"\x1bOQ",
    Qt.Key.Key_F3: b"\x1bOR",
    Qt.Key.Key_F4: b"\x1bOS",
    Qt.Key.Key_F5: b"\x1b[15~",
    Qt.Key.Key_F6: b"\x1b[17~",
    Qt.Key.Key_F7: b"\x1b[18~",
    Qt.Key.Key_F8: b"\x1b[19~",
    Qt.Key.Key_F9: b"\x1b[20~",
    Qt.Key.Key_F10: b"\x1b[21~",
    Qt.Key.Key_F11: b"\x1b[23~",
    Qt.Key.Key_F12: b"\x1b[24~",
}

_SIMPLE_SEQUENCES = {
    Qt.Key.Key_Backspace: b"\x7f",
    Qt.Key.Key_Tab: b"\t",
    Qt.Key.Key_Return: b"\r",
    Qt.Key.Key_Enter: b"\r",
    Qt.Key.Key_Escape: b"\x1b",
}


class KeyboardTranslator:
    """
    Converts :class:`QKeyEvent` instances into the byte sequences that
    should be written to the remote PTY.
    """

    def translate(
        self,
        event: QKeyEvent,
        application_cursor_keys: bool = False,
    ) -> bytes | None:
        """
        Translate a key press event into terminal bytes.

        Returns ``None`` if the event carries no terminal-meaningful
        payload (e.g. a bare modifier key press).
        """
        key = event.key()
        modifiers = event.modifiers()

        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if key == Qt.Key.Key_Tab and shift:
            return b"\x1b[Z"

        if key in _SIMPLE_SEQUENCES:
            return _SIMPLE_SEQUENCES[key]

        if key in _NAVIGATION_SEQUENCES:
            return _NAVIGATION_SEQUENCES[key]

        if key in _FUNCTION_SEQUENCES:
            return _FUNCTION_SEQUENCES[key]

        if key in _NORMAL_MODE_SEQUENCES:
            table = (
                _APPLICATION_MODE_SEQUENCES
                if application_cursor_keys
                else _NORMAL_MODE_SEQUENCES
            )
            return table[key]

        if ctrl:
            ctrl_bytes = self._translate_ctrl_combo(key)
            if ctrl_bytes is not None:
                return ctrl_bytes

        text = event.text()
        if text:
            return text.encode("utf-8", errors="replace")

        return None

    @staticmethod
    def _translate_ctrl_combo(key: int) -> bytes | None:
        """
        Translate Ctrl+<letter/punctuation> combinations to their
        corresponding control code, using the standard formula
        ``chr(key) - 64`` for A-Z (e.g. Ctrl+C -> 0x03, Ctrl+L -> 0x0c).
        """
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            return bytes([key - Qt.Key.Key_A + 1])

        if key == Qt.Key.Key_Space:
            return b"\x00"

        if key == Qt.Key.Key_BracketLeft:
            return b"\x1b"

        if key == Qt.Key.Key_Backslash:
            return b"\x1c"

        if key == Qt.Key.Key_BracketRight:
            return b"\x1d"

        if key == Qt.Key.Key_Underscore or key == Qt.Key.Key_Minus:
            return b"\x1f"

        return None
