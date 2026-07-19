"""
Manages the set of concurrently open SSH tabs within the SSH page.

This is the "SSH Controller" referenced in the architecture diagram:
it sits between the Inventory/quick-connect entry points and the
individual :class:`~netforge.modules.ssh.terminal_widget.SSHTerminalWidget`
tabs, each of which owns its own persistent
:class:`~netforge.core.terminal.session.SSHSession`.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QTabWidget, QWidget

from netforge.core.terminal.session import SSHSession
from netforge.core.terminal.worker import HostKeyPolicy
from netforge.models.connection import Connection
from netforge.modules.ssh.connect_dialog import SSHConnectDialog
from netforge.modules.ssh.terminal_widget import SSHTerminalWidget


class SSHController:
    """Owns the lifecycle of every open SSH tab inside one SSH page."""

    def __init__(self, tab_widget: QTabWidget) -> None:
        self.tab_widget = tab_widget

    # ------------------------------------------------------------------
    # Opening sessions.
    # ------------------------------------------------------------------

    def open_from_connection(self, connection: Connection) -> SSHTerminalWidget:
        """Open a new tab from a saved Inventory :class:`Connection` row."""
        host = connection.ip_address or connection.hostname
        label = f"{connection.username}@{connection.hostname or connection.ip_address}"

        return self._open_tab(
            label,
            host=host,
            port=connection.port or 22,
            username=connection.username,
            password=connection.password or None,
        )

    def open_quick_connect(self, parent: QWidget | None = None) -> SSHTerminalWidget | None:
        """Prompt for connection details and open a new ad hoc tab."""
        dialog = SSHConnectDialog(parent)

        if not dialog.exec():
            return None

        data = dialog.get_data()

        if not data["host"] or not data["username"]:
            QMessageBox.warning(
                parent,
                "Missing Information",
                "Host and username are required to connect.",
            )
            return None

        label = f"{data['username']}@{data['host']}"

        return self._open_tab(
            label,
            host=data["host"],
            port=data["port"],
            username=data["username"],
            password=data["password"],
            key_filename=data["key_filename"],
            passphrase=data["passphrase"],
            host_key_policy=data["host_key_policy"],
            timeout=data["timeout"],
        )

    def _open_tab(
        self,
        label: str,
        host: str,
        username: str,
        port: int = 22,
        password: str | None = None,
        key_filename: str | None = None,
        passphrase: str | None = None,
        host_key_policy: str = HostKeyPolicy.AUTO_ADD,
        timeout: float = 10.0,
    ) -> SSHTerminalWidget:
        session = SSHSession(
            host=host,
            port=port,
            username=username,
            password=password,
            key_filename=key_filename,
            passphrase=passphrase,
            timeout=timeout,
            host_key_policy=host_key_policy,
        )

        widget = SSHTerminalWidget(session, label)

        tab_label = self._unique_tab_label(label)
        index = self.tab_widget.addTab(widget, tab_label)
        self.tab_widget.setCurrentIndex(index)

        return widget

    def _unique_tab_label(self, base_label: str) -> str:
        existing = {self.tab_widget.tabText(i) for i in range(self.tab_widget.count())}

        if base_label not in existing:
            return base_label

        suffix = 2
        while f"{base_label} ({suffix})" in existing:
            suffix += 1

        return f"{base_label} ({suffix})"

    # ------------------------------------------------------------------
    # Closing sessions.
    # ------------------------------------------------------------------

    def close_tab(self, index: int) -> None:
        widget = self.tab_widget.widget(index)

        if widget is None:
            return

        self.tab_widget.removeTab(index)

        if isinstance(widget, SSHTerminalWidget):
            widget.cleanup()

        widget.deleteLater()

    def close_all(self) -> None:
        while self.tab_widget.count():
            self.close_tab(0)
