from PySide6.QtWidgets import QTabWidget
from PySide6.QtCore import Signal


class WorkspaceManager(QTabWidget):

    tab_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.on_tab_changed)

    def open_page(self, title, widget):
        # Check if tab already exists
        for i in range(self.count()):
            if self.tabText(i) == title:
                self.setCurrentIndex(i)
                return

        self.addTab(widget, title)
        self.setCurrentWidget(widget)
    
    def close_tab(self, index):

        widget = self.widget(index)

        self.removeTab(index)

        widget.deleteLater()

        if self.count() == 0:
            from ui.pages.dashboard.dashboard_page import DashboardPage

            self.open_page("Dashboard", DashboardPage())

    def on_tab_changed(self, index):

        if index == -1:
            return

        page_name = self.tabText(index)

        self.tab_changed.emit(page_name)