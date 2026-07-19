"""
The content of a single SSH tab: a status/action toolbar on top of a
:class:`~netforge.core.terminal.renderer.TerminalRenderer`, all wired
to one :class:`~netforge.core.terminal.session.SSHSession`.

This is the only place the SSH module actually touches the terminal
framework -- everything else in ``modules/ssh`` deals with tabs,
dialogs, and the inventory, not with rendering or PTY plumbing.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QWidget

from netforge.core.terminal.renderer import TerminalRenderer
from netforge.core.terminal.session import SessionState, SSHSession
from netforge.modules.ssh.toolbar import SSHSessionToolbar


class SSHTerminalWidget(QWidget):
    """
    One tab's worth of SSH UI: identity/status bar + live terminal,
    bound to a single, persistent :class:`SSHSession`.
    """

    def __init__(
        self,
        session: SSHSession,
        connection_label: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.session = session
        self.connection_label = connection_label

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = SSHSessionToolbar(connection_label)
        self.renderer = TerminalRenderer(session.emulator)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.renderer, 1)

        self._wire_signals()

        self.session.connect()

    def _wire_signals(self) -> None:
        # Renderer -> session (outgoing keystrokes/paste/resize).
        self.renderer.data_to_send.connect(self.session.send)
        self.renderer.size_changed.connect(self.session.resize)

        # Session -> renderer (incoming data repaints the screen).
        self.session.signals.screen_updated.connect(self.renderer.refresh)

        # Session -> toolbar (connection state).
        self.session.signals.state_changed.connect(self._on_state_changed)
        self.session.signals.error.connect(self._on_error)
        self.session.signals.logging_changed.connect(self.toolbar.set_logging)

        # Toolbar buttons -> session actions.
        self.toolbar.connect_btn.clicked.connect(self.session.connect)
        self.toolbar.disconnect_btn.clicked.connect(self.session.disconnect)
        self.toolbar.reconnect_btn.clicked.connect(self.session.reconnect)
        self.toolbar.log_btn.clicked.connect(self._on_log_toggled)

    def _on_log_toggled(self, checked: bool) -> None:
        if checked:
            self.session.start_logging()
        else:
            self.session.stop_logging()

    def _on_state_changed(self, state: SessionState) -> None:
        self.toolbar.set_state(state)
        if state == SessionState.CONNECTED:
            self.renderer.setFocus()

    def _on_error(self, kind: str, message: str) -> None:
        self.toolbar.show_error(message)

        if kind == "host_key":
            QMessageBox.warning(
                self,
                "Host Key Verification Failed",
                f"The host key presented by {self.session.host} did not match "
                f"a known key.\n\n{message}",
            )

    def cleanup(self) -> None:
        """Called by the page/controller when this tab is being closed."""
        self.session.cleanup()
