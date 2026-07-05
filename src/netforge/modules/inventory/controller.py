from netforge.modules.inventory.dialog import InventoryDialog
from netforge.services.connection_service import ConnectionService
from netforge.modules.inventory.details_dialog import ConnectionDetailsDialog
from PySide6.QtWidgets import QMessageBox


class InventoryController:

    def __init__(self, page):
        self.page = page
        self.service = ConnectionService()

        self.refresh()

    def new_connection(self):

        dialog = InventoryDialog()

        if dialog.exec():

            data = dialog.get_data()

            self.service.create_connection(data)

            self.refresh()

    def refresh(self):

        rows = self.service.get_all()

        self.page.model.load(rows)

    def selected_connection(self):

        indexes = self.page.table.selectionModel().selectedRows()

        if not indexes:
            return None

        row = indexes[0].row()

        return self.page.model.rows[row]
    
    def delete_connection(self):

        connection = self.selected_connection()

        if connection is None:
            return

        reply = QMessageBox.question(
            self.page,
            "Delete",
            f"Delete '{connection.name}' ?"
        )

        if reply == QMessageBox.StandardButton.Yes:

            self.service.delete(connection.id)

            self.refresh()

    def edit_connection(self):

        connection = self.selected_connection()

        if connection is None:
            return

        dialog = InventoryDialog(connection)

        if dialog.exec():

            self.service.update(
                connection.id,
                dialog.get_data()
            )

            self.refresh()

    def open_details(self):

        connection = self.selected_connection()

        if connection is None:
            return

        dialog = ConnectionDetailsDialog(connection)

        dialog.exec()            