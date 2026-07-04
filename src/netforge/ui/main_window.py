from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QWidget,
)

from netforge.ui.menu_bar import create_menu
from netforge.ui.navigation_rail import NavigationRail
from netforge.ui.status_bar import NetForgeStatusBar
from netforge.ui.workspace import Workspace
from netforge.ui.pages.dashboard.dashboard_page import DashboardPage
from netforge.ui.sidebar import Sidebar
from netforge.ui.page_manager import PageManager
from netforge.core.navigation_data import SIDEBAR_ITEMS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NetForge")

        self.resize(1600, 900)

        create_menu(self)

        self.setStatusBar(NetForgeStatusBar())

        self.build_ui()
        self.navigation_changed(0, "Dashboard")

    def build_ui(self):

        container = QWidget()

        layout = QHBoxLayout(container)

        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter()

        self.page_manager = PageManager()

        self.page_manager.workspace.tab_changed.connect(
        self.tab_changed
        )

        splitter.addWidget(self.page_manager.workspace)

        splitter.setStretchFactor(0, 1)

        self.navigation = NavigationRail()

        self.navigation.page_selected.connect(
        self.navigation_changed
        )

        layout.addWidget(self.navigation)

        self.sidebar = Sidebar()

        layout.addWidget(self.sidebar)

        layout.addWidget(splitter)

        self.setCentralWidget(container)

    def navigation_changed(self, index, page_name):

        self.page_manager.change_page(index)

        self.sidebar.load_items(
            SIDEBAR_ITEMS[page_name]
        )

    def tab_changed(self, page_name):

        from netforge.core.navigation_data import SIDEBAR_ITEMS

        self.sidebar.load_items(
            SIDEBAR_ITEMS[page_name]
        )