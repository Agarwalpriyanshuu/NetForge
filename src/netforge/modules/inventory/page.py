from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from netforge.modules.inventory.controller import InventoryController
from netforge.modules.inventory.table import InventoryTable
from netforge.modules.inventory.table_model import InventoryTableModel
from netforge.modules.inventory.toolbar import InventoryToolbar


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

        self.empty.setProperty("class", "emptyState")

        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.table)
        layout.addWidget(self.empty)
        layout.addWidget(self.status)

        self.controller = InventoryController(self)

        # The table and the "no devices" placeholder occupy the same
        # space in the layout; only one should ever be visible at a
        # time. QAbstractTableModel emits modelReset whenever
        # InventoryTableModel.load() runs, which is exactly when the
        # row count may have changed, so hook that directly rather
        # than requiring every caller of refresh() to remember to
        # update visibility.
        self.model.modelReset.connect(self._update_empty_state)
        self._update_empty_state()

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

    def _update_empty_state(self):
        count = len(self.model.rows)

        self.table.setVisible(count > 0)
        self.empty.setVisible(count == 0)
        self.status.setText(f"Total Devices : {count}")
