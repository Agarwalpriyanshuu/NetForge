"""
The Qt-facing half of the terminal framework: a widget that paints a
:class:`~netforge.core.terminal.emulator.TerminalEmulator`'s screen
buffer and turns keyboard/mouse/clipboard input into raw bytes.

This widget never touches the network. It only knows how to draw a
:class:`TerminalEmulator` and emit :attr:`data_to_send` -- whoever
owns it (normally an
:class:`~netforge.core.terminal.session.SSHSession`) is responsible
for actually shipping those bytes to the remote host and for calling
:meth:`refresh` whenever new data has been fed into the emulator.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QKeyEvent, QMouseEvent, QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QWidget

from netforge.core.terminal.clipboard import ClipboardManager
from netforge.core.terminal.colors import (
    TERMINAL_BACKGROUND,
    TERMINAL_CURSOR,
    TERMINAL_SELECTION,
    resolve_color,
)
from netforge.core.terminal.cursor import CursorTracker
from netforge.core.terminal.emulator import TerminalEmulator
from netforge.core.terminal.keyboard import KeyboardTranslator

_BLINK_INTERVAL_MS = 530

# Fonts tried in order; the first one available on the platform wins.
_PREFERRED_FONTS = [
    "Cascadia Mono",
    "Consolas",
    "JetBrains Mono",
    "DejaVu Sans Mono",
    "Courier New",
]


class TerminalRenderer(QWidget):
    """A single terminal viewport: paints an emulator and captures input."""

    # Raw bytes that should be sent to the remote shell.
    data_to_send = Signal(bytes)

    # The widget was resized to a new character grid.
    size_changed = Signal(int, int)  # cols, rows

    def __init__(self, emulator: TerminalEmulator, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.emulator = emulator
        self.keyboard = KeyboardTranslator()
        self.clipboard = ClipboardManager()
        self.cursor_tracker = CursorTracker(emulator)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setMouseTracking(True)

        self.setFont(self._build_font())

        metrics = QFontMetrics(self.font())
        self._char_width = max(1, metrics.horizontalAdvance("W"))
        self._char_height = max(1, metrics.height())
        self._ascent = metrics.ascent()

        self._selecting = False
        self._selection_start: tuple[int, int] | None = None
        self._selection_end: tuple[int, int] | None = None

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._on_blink)
        self._blink_timer.start(_BLINK_INTERVAL_MS)

        self.setMinimumSize(200, 100)

    # ------------------------------------------------------------------
    # Setup helpers.
    # ------------------------------------------------------------------

    @staticmethod
    def _build_font() -> QFont:
        font = QFont(_PREFERRED_FONTS[0])
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(11)

        for family in _PREFERRED_FONTS:
            candidate = QFont(family)
            candidate.setStyleHint(QFont.StyleHint.Monospace)
            if candidate.exactMatch() or family == _PREFERRED_FONTS[-1]:
                font = QFont(family)
                font.setStyleHint(QFont.StyleHint.Monospace)
                font.setFixedPitch(True)
                font.setPointSize(11)
                break

        return font

    def sizeHint(self) -> QSize:
        return QSize(
            self._char_width * self.emulator.columns,
            self._char_height * self.emulator.rows,
        )

    # ------------------------------------------------------------------
    # Painting.
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(TERMINAL_BACKGROUND))

        cols = self.emulator.columns
        rows = self.emulator.rows

        for row in range(rows):
            line = self.emulator.get_line(row)
            for col in range(cols):
                char = line[col]
                if char.data == " " and char.bg == "default" and not char.reverse:
                    continue
                self._paint_cell(painter, row, col, char)

        cursor_info = self.cursor_tracker.position()
        if cursor_info.visible and self.cursor_tracker.blink_on:
            self._paint_cursor(painter, cursor_info.row, cursor_info.col)

        if self._selection_start and self._selection_end:
            self._paint_selection(painter)

        painter.end()
        self.emulator.clear_dirty()

    def _paint_cell(self, painter: QPainter, row: int, col: int, char) -> None:
        x = col * self._char_width
        y = row * self._char_height

        fg_hex = resolve_color(char.fg, is_foreground=True)
        bg_hex = resolve_color(char.bg, is_foreground=False)

        if char.reverse:
            fg_hex, bg_hex = bg_hex, fg_hex

        if bg_hex != TERMINAL_BACKGROUND:
            painter.fillRect(x, y, self._char_width, self._char_height, QColor(bg_hex))

        if char.data and char.data != " ":
            font = painter.font()
            font.setBold(char.bold)
            font.setUnderline(char.underscore)
            font.setStrikeOut(char.strikethrough)
            painter.setFont(font)
            painter.setPen(QColor(fg_hex))
            painter.drawText(x, y + self._ascent, char.data)

    def _paint_cursor(self, painter: QPainter, row: int, col: int) -> None:
        x = col * self._char_width
        y = row * self._char_height
        color = QColor(TERMINAL_CURSOR)

        if self.hasFocus():
            painter.fillRect(x, y, self._char_width, self._char_height, color)

            line = self.emulator.get_line(row)
            char = line[col]
            if char.data and char.data != " ":
                painter.setPen(QColor(TERMINAL_BACKGROUND))
                painter.drawText(x, y + self._ascent, char.data)
        else:
            pen = QPen(color)
            painter.setPen(pen)
            painter.drawRect(x, y, self._char_width - 1, self._char_height - 1)

    def _paint_selection(self, painter: QPainter) -> None:
        (sr, sc), (er, ec) = self._normalized_selection()

        color = QColor(TERMINAL_SELECTION)
        color.setAlpha(120)

        for row in range(sr, er + 1):
            col_start = sc if row == sr else 0
            col_end = ec if row == er else self.emulator.columns

            x = col_start * self._char_width
            y = row * self._char_height
            width = max(0, (col_end - col_start)) * self._char_width

            painter.fillRect(x, y, width, self._char_height, color)

    # ------------------------------------------------------------------
    # Resize.
    # ------------------------------------------------------------------

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        cols = max(1, self.width() // self._char_width)
        rows = max(1, self.height() // self._char_height)

        if cols != self.emulator.columns or rows != self.emulator.rows:
            self.emulator.resize(cols, rows)
            self.size_changed.emit(cols, rows)

        self.update()

    # ------------------------------------------------------------------
    # Keyboard input.
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        modifiers = event.modifiers()

        is_ctrl_shift = bool(
            modifiers & Qt.KeyboardModifier.ControlModifier
            and modifiers & Qt.KeyboardModifier.ShiftModifier
        )

        if is_ctrl_shift and event.key() == Qt.Key.Key_C:
            self._copy_selection()
            return

        if is_ctrl_shift and event.key() == Qt.Key.Key_V:
            self._paste_clipboard()
            return

        data = self.keyboard.translate(event)

        if data is not None:
            self.cursor_tracker.reset_blink()
            self._clear_selection()
            if self.emulator.is_scrolled_back:
                self.emulator.scroll_to_bottom()
            self.data_to_send.emit(data)
            self.update()
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Mouse input: scrollback + selection.
    # ------------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        moved = False

        if delta > 0:
            moved = self.emulator.scroll_up()
        elif delta < 0:
            moved = self.emulator.scroll_down()

        if moved:
            self.update()

        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            cell = self._pixel_to_cell(event.position().toPoint())
            self._selecting = True
            self._selection_start = cell
            self._selection_end = cell
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            if self._selection_start and self._selection_end and self._selection_start != self._selection_end:
                self._copy_selection()
                self._clear_selection()
            else:
                self._paste_clipboard()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._selecting:
            self._selection_end = self._pixel_to_cell(event.position().toPoint())
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._selecting = False

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            row, col = self._pixel_to_cell(event.position().toPoint())
            start_col, end_col = self._word_bounds(row, col)
            self._selection_start = (row, start_col)
            self._selection_end = (row, end_col)
            self.update()

    def _pixel_to_cell(self, point) -> tuple[int, int]:
        col = max(0, min(self.emulator.columns - 1, point.x() // self._char_width))
        row = max(0, min(self.emulator.rows - 1, point.y() // self._char_height))
        return row, col

    def _word_bounds(self, row: int, col: int) -> tuple[int, int]:
        display = self.emulator.get_display()
        if row >= len(display):
            return col, col

        line = display[row]
        start = col
        end = col

        while start > 0 and start - 1 < len(line) and not line[start - 1].isspace():
            start -= 1

        while end < len(line) - 1 and not line[end + 1].isspace():
            end += 1

        return start, end

    def _normalized_selection(self) -> tuple[tuple[int, int], tuple[int, int]]:
        start = self._selection_start
        end = self._selection_end
        if start <= end:
            return start, end
        return end, start

    def _clear_selection(self) -> None:
        self._selection_start = None
        self._selection_end = None

    # ------------------------------------------------------------------
    # Clipboard.
    # ------------------------------------------------------------------

    def _copy_selection(self) -> None:
        text = self.get_selected_text()
        if text:
            self.clipboard.copy(text)

    def _paste_clipboard(self) -> None:
        data = self.clipboard.paste_bytes()
        if data:
            self.data_to_send.emit(data)

    def get_selected_text(self) -> str:
        if not self._selection_start or not self._selection_end:
            return ""

        (sr, sc), (er, ec) = self._normalized_selection()
        display = self.emulator.get_display()
        lines: list[str] = []

        for row in range(sr, er + 1):
            line_text = display[row] if row < len(display) else ""
            col_start = sc if row == sr else 0
            col_end = (ec + 1) if row == er else len(line_text)
            lines.append(line_text[col_start:col_end])

        return "\n".join(line.rstrip() for line in lines)

    # ------------------------------------------------------------------
    # External hooks.
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Slot: connect to ``session.signals.screen_updated``."""
        self.update()

    def _on_blink(self) -> None:
        self.cursor_tracker.toggle_blink()
        self.update()
