from PySide6.QtWidgets import (
    QTableView,
    QHeaderView,
)

from netforge.modules.inventory.inventory_model import InventoryTableModel


class InventoryTable(QTableView):

    def __init__(self):
        super().__init__()

        self.model = InventoryTableModel()

        self.setModel(self.model)

        self.setSortingEnabled(True)

        self.setAlternatingRowColors(True)

        self.verticalHeader().hide()

        self.horizontalHeader().setStretchLastSection(True)

        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )

        self.setSelectionMode(
            QTableView.SelectionMode.SingleSelection
        )