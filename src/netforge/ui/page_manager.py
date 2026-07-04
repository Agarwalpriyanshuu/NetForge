from netforge.ui.workspace_manager import WorkspaceManager

from netforge.ui.pages.dashboard.dashboard_page import DashboardPage
from netforge.modules.ssh.page import SSHPage
from netforge.modules.inventory.page import InventoryPage
from netforge.ui.pages.packet_lab.packet_lab_page import PacketLabPage
from netforge.ui.pages.settings.settings_page import SettingsPage


class PageManager:

    def __init__(self):

        self.workspace = WorkspaceManager()

        self.pages = {
            0: ("Dashboard", DashboardPage),
            1: ("Inventory", InventoryPage),
            2: ("SSH", SSHPage),
            3: ("Packet Lab", PacketLabPage),
            4: ("Settings", SettingsPage),
        }

        # Open Dashboard on startup
        self.change_page(0)

    def change_page(self, index):

        title, page = self.pages[index]

        self.workspace.open_page(title, page())