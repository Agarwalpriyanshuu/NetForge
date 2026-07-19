from PySide6.QtCore import Qt
from PySide6.QtCore import QAbstractTableModel


class InventoryTableModel(QAbstractTableModel):

    headers = [
        "Name",
        "Hostname",
        "IP Address",
        "Username",
        "Protocol",
        "Port",
    ]

    def __init__(self):
        super().__init__()

        self.rows = []

    def load(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.rows)

    def columnCount(self, parent=None):
        return len(self.headers)

    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return

        if orientation == Qt.Horizontal:
            return self.headers[section]

    def data(self, index, role):

        if role != Qt.DisplayRole:
            return

        row = self.rows[index.row()]

        values = [
            row.name,
            row.hostname,
            row.ip_address,
            row.username,
            row.protocol,
            str(row.port),
        ]

        return values[index.column()]