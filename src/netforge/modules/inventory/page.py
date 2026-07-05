from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

from netforge.modules.inventory.toolbar import InventoryToolbar
from netforge.modules.inventory.table import InventoryTable
from netforge.modules.inventory.controller import InventoryController
from netforge.modules.inventory.table_model import InventoryTableModel
from PySide6.QtCore import Qt


class InventoryPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.toolbar = InventoryToolbar()

        self.table = InventoryTable()

        self.model = InventoryTableModel()

        self.table.setModel(self.model)

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

        self.controller = InventoryController(self)

        self.toolbar.new_btn.clicked.connect(
            self.controller.new_connection
        )

        self.toolbar.refresh_btn.clicked.connect(
            self.controller.refresh
        )

        self.toolbar.delete_btn.clicked.connect(
            self.controller.delete_connection
        )  

        self.toolbar.edit_btn.clicked.connect(
            self.controller.edit_connection
        ) 

        self.table.doubleClicked.connect(
            self.controller.open_details
        )