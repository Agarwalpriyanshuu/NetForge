"""
Protocol-agnostic terminal state machine.

Wraps a :class:`pyte.HistoryScreen` + :class:`pyte.ByteStream` pair.
This class has no knowledge of SSH, Paramiko, or Qt -- it simply
turns a stream of raw terminal bytes into a screen buffer that a
renderer can paint. Any future module that needs a terminal (Telnet,
Serial Console, local shell) can reuse this unchanged.
"""

from __future__ import annotations

import pyte

# Default scrollback size, in lines.
DEFAULT_HISTORY = 5000
DEFAULT_HISTORY_RATIO = 0.5


class TerminalEmulator:
    """
    A single terminal screen buffer with scrollback history.

    :param cols: initial width, in character columns.
    :param rows: initial height, in character rows.
    :param history: number of scrollback lines to retain.
    """

    def __init__(
        self,
        cols: int = 80,
        rows: int = 24,
        history: int = DEFAULT_HISTORY,
    ) -> None:
        self.screen = pyte.HistoryScreen(
            cols, rows, history=history, ratio=DEFAULT_HISTORY_RATIO
        )
        self.stream = pyte.ByteStream(self.screen)

    # ------------------------------------------------------------------
    # Feeding data in.
    # ------------------------------------------------------------------

    def feed(self, data: bytes) -> None:
        """Feed a chunk of raw bytes received from the remote PTY."""
        self.stream.feed(data)

    def resize(self, cols: int, rows: int) -> None:
        """Resize the emulated screen to new dimensions."""
        if cols <= 0 or rows <= 0:
            return
        self.screen.resize(lines=rows, columns=cols)

    def reset(self) -> None:
        """Reset the screen to its initial blank state."""
        self.screen.reset()

    # ------------------------------------------------------------------
    # Reading state out, for the renderer.
    # ------------------------------------------------------------------

    @property
    def columns(self) -> int:
        return self.screen.columns

    @property
    def rows(self) -> int:
        return self.screen.lines

    @property
    def title(self) -> str:
        return getattr(self.screen, "title", "")

    @property
    def cursor(self):
        """The pyte Cursor object (has ``.x``, ``.y``, ``.hidden``)."""
        return self.screen.cursor

    def get_line(self, row: int):
        """
        Return the sparse ``column -> Char`` mapping for a given
        on-screen row, suitable for iterating during a paint pass.
        """
        return self.screen.buffer[row]

    def get_display(self) -> list[str]:
        """Return the current screen contents as a list of plain strings."""
        return self.screen.display

    def dirty_rows(self) -> set[int]:
        """Row indices that changed since the last time they were cleared."""
        return self.screen.dirty

    def clear_dirty(self) -> None:
        self.screen.dirty.clear()

    def history_length(self) -> int:
        """Total number of lines currently retained above the viewport."""
        return len(self.screen.history.top)

    def scroll_up(self) -> bool:
        """
        Scroll the viewport up (towards older history) by one page.
        Returns True if the view actually moved.
        """
        if not self.screen.history.top:
            return False
        self.screen.prev_page()
        return True

    def scroll_down(self) -> bool:
        """
        Scroll the viewport down (towards live output) by one page.
        Returns True if the view actually moved.
        """
        if self.screen.history.position >= self.screen.history.size:
            return False
        self.screen.next_page()
        return True

    def scroll_to_bottom(self) -> None:
        """Jump the viewport back to the live, bottom-most position."""
        while self.screen.history.position < self.screen.history.size:
            self.screen.next_page()

    @property
    def is_scrolled_back(self) -> bool:
        return self.screen.history.position < self.screen.history.size
