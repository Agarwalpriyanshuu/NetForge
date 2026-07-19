import sys

from PySide6.QtWidgets import QApplication

from netforge.core.theme import apply_theme
from netforge.ui.main_window import MainWindow


class NetForgeApplication:

    def __init__(self):
        self.app = QApplication(sys.argv)

        self.app.setApplicationName("NetForge")
        self.app.setOrganizationName("NetForge")
        self.app.setApplicationVersion("0.0.1")

        apply_theme(self.app)

        self.window = MainWindow()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec())