"""
The SSH module's top-level page: a page-level toolbar for starting
new sessions, plus a tab strip holding every currently open SSH
terminal.

Sessions can be opened two ways:

    * "New Connection" button -> :class:`SSHConnectDialog` (ad hoc).
    * Inventory's "SSH" action -> :attr:`EventBus.open_ssh_requested`.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QTabWidget, QVBoxLayout, QWidget

from netforge.core.event_bus import EventBus
from netforge.models.connection import Connection
from netforge.modules.ssh.controller import SSHController
from netforge.ui.components.primary_button import PrimaryButton


class SSHPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 8, 8, 8)

        self.new_connection_btn = PrimaryButton("➕ New Connection")

        top_layout.addWidget(self.new_connection_btn)
        top_layout.addStretch()

        self.tabs = QTabWidget()
        self.tabs.setObjectName("sshSessionTabs")
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)

        layout.addWidget(top_bar)
        layout.addWidget(self.tabs, 1)

        self.controller = SSHController(self.tabs)

        self.new_connection_btn.clicked.connect(
            lambda: self.controller.open_quick_connect(self)
        )

        self.tabs.tabCloseRequested.connect(self.controller.close_tab)

        EventBus.instance().open_ssh_requested.connect(self._on_open_ssh_requested)

    def _on_open_ssh_requested(self, connection: Connection) -> None:
        self.controller.open_from_connection(connection)

    def cleanup(self) -> None:
        """
        Called by the workspace when the SSH page's outer tab itself
        is closed, to ensure every background worker thread and
        socket is shut down rather than orphaned.
        """
        self.controller.close_all()
