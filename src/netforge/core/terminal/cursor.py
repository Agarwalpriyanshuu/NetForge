"""
Cursor position/visibility tracking for the terminal renderer.

Separated out from :mod:`~netforge.core.terminal.renderer` so the
blink state machine and position math can be unit tested without a
Qt widget, and reused by any alternate renderer implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

from netforge.core.terminal.emulator import TerminalEmulator


@dataclass(frozen=True)
class CursorInfo:
    """A snapshot of the terminal cursor's current state."""

    row: int
    col: int
    visible: bool


class CursorTracker:
    """
    Tracks the emulator's cursor position and drives the on/off blink
    state used by the renderer's paint loop.
    """

    def __init__(self, emulator: TerminalEmulator) -> None:
        self._emulator = emulator
        self._blink_on = True

    def position(self) -> CursorInfo:
        """
        Return the cursor's current row/column and whether it should
        be drawn at all right now (hidden by the application, or the
        viewport is scrolled back into history).
        """
        cursor = self._emulator.cursor

        visible = (
            not cursor.hidden
            and not self._emulator.is_scrolled_back
        )

        return CursorInfo(row=cursor.y, col=cursor.x, visible=visible)

    def toggle_blink(self) -> bool:
        """
        Flip the blink phase. Intended to be called from a ``QTimer``
        on a fixed interval. Returns the new blink-on state.
        """
        self._blink_on = not self._blink_on
        return self._blink_on

    def reset_blink(self) -> None:
        """Force the cursor to be visible (used after any keystroke)."""
        self._blink_on = True

    @property
    def blink_on(self) -> bool:
        return self._blink_on
