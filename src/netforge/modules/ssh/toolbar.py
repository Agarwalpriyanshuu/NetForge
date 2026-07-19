"""
Per-session toolbar shown above each SSH terminal tab: connection
identity, live status, and Connect/Disconnect/Reconnect actions.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from netforge.core.terminal.session import SessionState

_STATE_LABELS = {
    SessionState.IDLE: "Idle",
    SessionState.CONNECTING: "Connecting…",
    SessionState.CONNECTED: "Connected",
    SessionState.DISCONNECTED: "Disconnected",
    SessionState.RECONNECTING: "Reconnecting…",
    SessionState.ERROR: "Error",
}

_STATE_COLORS = {
    SessionState.IDLE: "#9d9d9d",
    SessionState.CONNECTING: "#e5c07b",
    SessionState.CONNECTED: "#23d18b",
    SessionState.DISCONNECTED: "#9d9d9d",
    SessionState.RECONNECTING: "#e5c07b",
    SessionState.ERROR: "#f14c4c",
}


class SSHSessionToolbar(QWidget):
    """
    A compact status/action row bound to a single SSH tab. The buttons
    only emit clicked signals -- :mod:`terminal_widget` is responsible
    for wiring them to the actual :class:`SSHSession` methods.
    """

    def __init__(self, connection_label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.host_label = QLabel(connection_label)
        self.host_label.setStyleSheet("font-weight: 600;")

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {_STATE_COLORS[SessionState.IDLE]};")

        self.status_label = QLabel(_STATE_LABELS[SessionState.IDLE])

        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.reconnect_btn = QPushButton("Reconnect")

        self.log_btn = QPushButton("📝 Start Logging")
        self.log_btn.setCheckable(True)
        self.log_btn.setToolTip("Log this session's output to a timestamped file on disk.")

        self.disconnect_btn.setEnabled(False)
        self.reconnect_btn.setEnabled(False)

        layout.addWidget(self.host_label)
        layout.addSpacing(12)
        layout.addWidget(self.status_dot)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.log_btn)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.disconnect_btn)
        layout.addWidget(self.reconnect_btn)

    def set_state(self, state: SessionState) -> None:
        self.status_label.setText(_STATE_LABELS.get(state, str(state)))
        self.status_dot.setStyleSheet(f"color: {_STATE_COLORS.get(state, '#9d9d9d')};")

        busy_states = (SessionState.CONNECTING, SessionState.RECONNECTING)

        self.connect_btn.setEnabled(state not in (SessionState.CONNECTED,) and state not in busy_states)
        self.disconnect_btn.setEnabled(state == SessionState.CONNECTED)
        self.reconnect_btn.setEnabled(
            state in (SessionState.CONNECTED, SessionState.DISCONNECTED, SessionState.ERROR)
        )

    def show_error(self, message: str) -> None:
        self.status_label.setText(f"Error: {message}")
        self.status_label.setToolTip(message)
        self.status_dot.setStyleSheet(f"color: {_STATE_COLORS[SessionState.ERROR]};")

    def set_logging(self, enabled: bool, path=None) -> None:
        self.log_btn.blockSignals(True)
        self.log_btn.setChecked(enabled)
        self.log_btn.blockSignals(False)

        if enabled and path is not None:
            self.log_btn.setText("⏹ Stop Logging")
            self.log_btn.setToolTip(f"Logging to {path}")
        else:
            self.log_btn.setText("📝 Start Logging")
            self.log_btn.setToolTip(
                "Log this session's output to a timestamped file on disk."
            )
