from PySide6.QtCore import Qt
from PySide6.QtCore import QAbstractTableModel


class InventoryTableModel(QAbstractTableModel):

    HEADERS = [
        "★",
        "Name",
        "Hostname",
        "Username",
        "Protocol",
        "Port",
        "Tags",
        "Status",
    ]

    def __init__(self):
        super().__init__()

        self.rows = []

    def rowCount(self, parent=None):
        return len(self.rows)

    def columnCount(self, parent=None):
        return len(self.HEADERS)

    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.HEADERS[section]

        return str(section + 1)

    def data(self, index, role):

        if not index.isValid():
            return None

        if role == Qt.DisplayRole:

            return self.rows[index.row()][index.column()]

        return None