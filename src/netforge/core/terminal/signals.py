"""
Signal definitions used to move data safely across thread boundaries
in the NetForge terminal framework.

Qt signal/slot connections are thread-safe by default when the
receiving object lives on a different thread than the emitting one
(Qt automatically queues the delivery). Every piece of the terminal
framework that touches the network runs on a background
:class:`~netforge.core.terminal.worker.SSHWorker` thread, and every
piece that touches the UI (the renderer, toolbars, dialogs) must only
ever be driven from signals -- never called directly from the worker
thread.

``WorkerSignals`` are owned by the worker/background thread.
``SessionSignals`` are owned by the session and are what the UI layer
should actually connect to.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class WorkerSignals(QObject):
    """Signals emitted from inside :class:`SSHWorker`'s background thread."""

    # Raw bytes received from the remote PTY.
    data_received = Signal(bytes)

    # The shell channel was successfully opened.
    connected = Signal()

    # The connection ended. Carries a human-readable reason.
    disconnected = Signal(str)

    # A connection-level error occurred before/instead of connecting.
    # Carries (error_kind, message), where error_kind is one of:
    # "timeout", "auth", "unreachable", "refused", "host_key", "unknown".
    error = Signal(str, str)


class SessionSignals(QObject):
    """
    Signals emitted by :class:`~netforge.core.terminal.session.SSHSession`.

    This is the signal surface the UI layer (renderer, toolbar, tab
    label, status bar) should connect to. It is intentionally a
    superset/refinement of ``WorkerSignals`` so the UI never has to
    reach into the worker thread's objects directly.
    """

    # The pyte screen buffer changed and should be repainted.
    screen_updated = Signal()

    # Session state machine transitioned. Carries the new SessionState.
    state_changed = Signal(object)

    # An error occurred. Carries (error_kind, message).
    error = Signal(str, str)

    # The remote set a new terminal title via OSC escape sequence.
    title_changed = Signal(str)

    # The terminal bell (\x07) was triggered.
    bell = Signal()

    # Session logging was started or stopped. Carries (enabled, path),
    # where path is a pathlib.Path when enabled is True, else None.
    logging_changed = Signal(bool, object)
