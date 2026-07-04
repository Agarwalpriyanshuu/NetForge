from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

from netforge.modules.inventory.toolbar import InventoryToolbar
from netforge.modules.inventory.table import InventoryTable
from PySide6.QtCore import Qt


class InventoryPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.toolbar = InventoryToolbar()

        self.table = InventoryTable()

        self.status = QLabel("Total Devices : 0")

        self.empty = QLabel(
            "No devices found.\n\nClick 'New Device' to add your first inventory item."
        )

        self.empty.setStyleSheet("""
            QLabel{
                color:gray;
                font-size:14px;
            }
        """)

        self.empty.setAlignment(Qt.AlignCenter)  

        layout.addWidget(self.toolbar)
        layout.addWidget(self.table)
        layout.addWidget(self.status)
        layout.addWidget(self.empty)
      