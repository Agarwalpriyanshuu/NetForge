from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
)


class NavigationRail(QListWidget):
    page_selected = Signal(int, str)
    
    def __init__(self):
        super().__init__()

        self.setObjectName("navigationRail")

        self.setFixedWidth(70)

        self.setSpacing(8)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        items = [ 
            ("🏠", "Dashboard"), 
            ("📚", "Inventory"),
            ("🖥", "SSH"),
            ("📦", "Packet Lab"), 
            ("⚙", "Settings"), 
        ]
        self.page_names = [
            "Dashboard",
            "Inventory",
            "SSH",
            "Packet Lab",
            "Settings",
        ]

        for icon, text in items:
            item = QListWidgetItem(icon)
            item.setToolTip(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.addItem(item)

        self.setCurrentRow(0)
        self.currentRowChanged.connect(self.navigation_changed)
    
    def navigation_changed(self, index):

        page_name = self.page_names[index]

        self.page_selected.emit(index, page_name)