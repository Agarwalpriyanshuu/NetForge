from ui.workspace_manager import WorkspaceManager

from ui.pages.dashboard.dashboard_page import DashboardPage
from ui.pages.network.network_page import NetworkPage
from ui.pages.remote.remote_page import RemotePage
from ui.pages.packet_lab.packet_lab_page import PacketLabPage
from ui.pages.settings.settings_page import SettingsPage


class PageManager:

    def __init__(self):

        self.workspace = WorkspaceManager()

        self.pages = {
            0: ("Dashboard", DashboardPage),
            1: ("Network", NetworkPage),
            2: ("Remote", RemotePage),
            3: ("Packet Lab", PacketLabPage),
            4: ("Settings", SettingsPage),
        }

        # Open Dashboard on startup
        self.change_page(0)

    def change_page(self, index):

        title, page = self.pages[index]

        self.workspace.open_page(title, page())