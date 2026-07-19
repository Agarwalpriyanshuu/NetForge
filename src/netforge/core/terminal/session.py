"""
Orchestrates a single interactive SSH session: the background worker
thread, the terminal emulator state machine, and the high-level
signal surface the UI reacts to.

This is the main entry point the SSH module (and any future module
reusing this framework) should use. Consumers should not talk to
:class:`~netforge.core.terminal.worker.SSHWorker` directly.
"""

from __future__ import annotations

import enum
from pathlib import Path

from PySide6.QtCore import QObject, QTimer

from netforge.core.terminal.emulator import TerminalEmulator
from netforge.core.terminal.session_logger import SessionLogger
from netforge.core.terminal.signals import SessionSignals
from netforge.core.terminal.worker import HostKeyPolicy, SSHWorker

# How long to wait, in milliseconds, before a reconnect attempt after
# disconnect() completes, to give sockets time to fully tear down.
_RECONNECT_DELAY_MS = 500

# How long to wait for the worker thread to finish after stop(), before
# giving up and moving on (it is a daemon-style QThread so this is a
# safety margin, not a hard requirement).
_WORKER_STOP_TIMEOUT_MS = 3000


class SessionState(enum.Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class SSHSession(QObject):
    """
    A single, reusable, persistent SSH session.

    :param host: hostname or IP address.
    :param port: TCP port.
    :param username: SSH username.
    :param password: SSH password (ignored if ``key_filename`` is set).
    :param key_filename: path to a private key file, for key-based auth.
    :param passphrase: private key passphrase, if any.
    :param timeout: connection timeout, in seconds.
    :param cols: initial terminal width.
    :param rows: initial terminal height.
    :param host_key_policy: one of :class:`~netforge.core.terminal.worker.HostKeyPolicy`.
    """

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        password: str | None = None,
        key_filename: str | None = None,
        passphrase: str | None = None,
        timeout: float = 10.0,
        cols: int = 80,
        rows: int = 24,
        host_key_policy: str = HostKeyPolicy.AUTO_ADD,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.passphrase = passphrase
        self.timeout = timeout
        self.host_key_policy = host_key_policy

        self.signals = SessionSignals()
        self.emulator = TerminalEmulator(cols=cols, rows=rows)

        self._state = SessionState.IDLE
        self._worker: SSHWorker | None = None
        self._auto_reconnect = False
        self._pending_reconnect_timer: QTimer | None = None
        self._logger: SessionLogger | None = None

    # ------------------------------------------------------------------
    # State.
    # ------------------------------------------------------------------

    @property
    def state(self) -> SessionState:
        return self._state

    def _set_state(self, state: SessionState) -> None:
        self._state = state
        self.signals.state_changed.emit(state)

    # ------------------------------------------------------------------
    # Lifecycle.
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the connection. Safe to call again after disconnect()."""
        if self._state in (SessionState.CONNECTING, SessionState.CONNECTED):
            return

        self._set_state(SessionState.CONNECTING)

        self._worker = SSHWorker(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            key_filename=self.key_filename,
            passphrase=self.passphrase,
            timeout=self.timeout,
            cols=self.emulator.columns,
            rows=self.emulator.rows,
            host_key_policy=self.host_key_policy,
        )

        self._worker.signals.data_received.connect(self._on_data_received)
        self._worker.signals.connected.connect(self._on_connected)
        self._worker.signals.disconnected.connect(self._on_disconnected)
        self._worker.signals.error.connect(self._on_error)

        self._worker.start()

    def disconnect(self) -> None:
        """Gracefully close the connection. Does not destroy the session."""
        self._auto_reconnect = False

        if self._worker is not None:
            self._worker.stop()
            self._worker.wait(_WORKER_STOP_TIMEOUT_MS)
            self._worker = None

        if self._state != SessionState.ERROR:
            self._set_state(SessionState.DISCONNECTED)

    def reconnect(self) -> None:
        """Disconnect (if connected) and reconnect after a short delay."""
        self._set_state(SessionState.RECONNECTING)

        if self._worker is not None:
            self._worker.stop()
            self._worker.wait(_WORKER_STOP_TIMEOUT_MS)
            self._worker = None

        self._pending_reconnect_timer = QTimer(self)
        self._pending_reconnect_timer.setSingleShot(True)
        self._pending_reconnect_timer.timeout.connect(self.connect)
        self._pending_reconnect_timer.start(_RECONNECT_DELAY_MS)

    def cleanup(self) -> None:
        """
        Fully tear down the session. Call this when the owning tab is
        closed or the application is exiting.
        """
        self._auto_reconnect = False

        if self._pending_reconnect_timer is not None:
            self._pending_reconnect_timer.stop()
            self._pending_reconnect_timer = None

        if self._worker is not None:
            self._worker.stop()
            self._worker.wait(_WORKER_STOP_TIMEOUT_MS)
            self._worker = None

        if self._logger is not None:
            self._logger.stop()
            self._logger = None

    # ------------------------------------------------------------------
    # I/O.
    # ------------------------------------------------------------------

    def send(self, data: bytes) -> None:
        """Send raw bytes to the remote shell (e.g. from a keypress)."""
        if self._worker is not None and self._state == SessionState.CONNECTED:
            self._worker.send(data)

    def resize(self, cols: int, rows: int) -> None:
        """Resize both the local emulator and the remote PTY."""
        self.emulator.resize(cols, rows)

        if self._worker is not None:
            self._worker.resize(cols, rows)

    # ------------------------------------------------------------------
    # Session logging.
    # ------------------------------------------------------------------

    @property
    def is_logging(self) -> bool:
        return self._logger is not None and self._logger.is_active

    def start_logging(self) -> Path:
        """
        Start writing this session's output to a timestamped log file
        on disk. Safe to call across reconnects -- the same log file
        stays open and simply records connect/disconnect markers.
        """
        if self._logger is None:
            self._logger = SessionLogger(self.host, self.username)

        path = self._logger.start()
        self.signals.logging_changed.emit(True, path)
        return path

    def stop_logging(self) -> None:
        """Stop and close the session log file, if one is open."""
        if self._logger is not None:
            self._logger.stop()

        self.signals.logging_changed.emit(False, None)

    # ------------------------------------------------------------------
    # Worker signal handlers. These run on the main/UI thread -- Qt
    # marshals the cross-thread signal emission for us -- so it is
    # safe to touch self.emulator and emit our own UI-facing signals
    # from here.
    # ------------------------------------------------------------------

    def _on_data_received(self, data: bytes) -> None:
        previous_title = self.emulator.title

        self.emulator.feed(data)

        if self._logger is not None and self._logger.is_active:
            self._logger.write(data)

        new_title = self.emulator.title
        if new_title and new_title != previous_title:
            self.signals.title_changed.emit(new_title)

        if b"\x07" in data:
            self.signals.bell.emit()

        self.signals.screen_updated.emit()

    def _on_connected(self) -> None:
        self._set_state(SessionState.CONNECTED)

        if self._logger is not None and self._logger.is_active:
            self._logger.mark(f"Connected to {self.host}:{self.port}")

    def _on_disconnected(self, reason: str) -> None:
        if self._state != SessionState.ERROR:
            self._set_state(SessionState.DISCONNECTED)

        if self._logger is not None and self._logger.is_active:
            self._logger.mark(f"Disconnected: {reason}")

    def _on_error(self, kind: str, message: str) -> None:
        self._set_state(SessionState.ERROR)
        self.signals.error.emit(kind, message)
