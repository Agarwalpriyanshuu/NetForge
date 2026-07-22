"""
The Diagnostics module's top-level page: Ping, Traceroute, DNS
Lookup, and Port Scanner as tabs within one page, matching the
troubleshooting-first priority of getting these fast, common tools
in front of the user without a lot of navigation overhead.
"""

from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from netforge.modules.diagnostics.dns_tool import DnsLookupPanel
from netforge.modules.diagnostics.ping_tool import PingPanel
from netforge.modules.diagnostics.port_scanner_tool import PortScannerPanel
from netforge.modules.diagnostics.traceroute_tool import TraceroutePanel


class DiagnosticsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("diagnosticsTabs")
        self.tabs.setDocumentMode(True)

        self.ping_panel = PingPanel()
        self.traceroute_panel = TraceroutePanel()
        self.dns_panel = DnsLookupPanel()
        self.port_scanner_panel = PortScannerPanel()

        self.tabs.addTab(self.ping_panel, "Ping")
        self.tabs.addTab(self.traceroute_panel, "Traceroute")
        self.tabs.addTab(self.dns_panel, "DNS Lookup")
        self.tabs.addTab(self.port_scanner_panel, "Port Scanner")

        layout.addWidget(self.tabs)

    def cleanup(self) -> None:
        """
        Called by the workspace when this page's outer tab is closed,
        so any in-flight ping/traceroute/scan background threads are
        stopped rather than orphaned.
        """
        self.ping_panel.cleanup()
        self.traceroute_panel.cleanup()
        self.dns_panel.cleanup()
        self.port_scanner_panel.cleanup()
