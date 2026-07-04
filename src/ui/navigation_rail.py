from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
)


class NavigationRail(QListWidget):
    def __init__(self):
        super().__init__()

        self.setFixedWidth(70)

        self.setSpacing(8)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        items = [
            ("🏠", "Dashboard"),
            ("💼", "Workspace"),
            ("🌐", "Network"),
            ("🖥", "Remote"),
            ("🔍", "Diagnostics"),
            ("📦", "Packet Lab"),
            ("🛠", "Utilities"),
            ("📄", "Reports"),
            ("⚙", "Settings"),
        ]

        for icon, text in items:
            item = QListWidgetItem(icon)
            item.setToolTip(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.addItem(item)

        self.setCurrentRow(0)