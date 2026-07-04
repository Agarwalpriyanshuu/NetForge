from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QWidget,
)

from ui.menu_bar import create_menu
from ui.navigation_rail import NavigationRail
from ui.status_bar import NetForgeStatusBar
from ui.workspace import Workspace


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NetForge")

        self.resize(1600, 900)

        create_menu(self)

        self.setStatusBar(NetForgeStatusBar())

        self.build_ui()

    def build_ui(self):

        container = QWidget()

        layout = QHBoxLayout(container)

        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter()

        splitter.addWidget(Workspace())

        splitter.setStretchFactor(0, 1)

        layout.addWidget(NavigationRail())

        layout.addWidget(splitter)

        self.setCentralWidget(container)