"""
A tiny application-wide event bus used to decouple modules from one
another -- for example, letting the Inventory module ask the SSH
module to open a connection without either module importing the
other's internals directly.

This keeps the "Inventory -> Open SSH -> SSH Controller" flow clean:
Inventory only needs to know that a request exists, not how the SSH
module chooses to fulfil it.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    """Process-wide singleton signal hub."""

    # Emitted when the user wants to open an SSH session for a given
    # inventory Connection record.
    open_ssh_requested = Signal(object)

    _instance: "EventBus | None" = None

    @classmethod
    def instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance
