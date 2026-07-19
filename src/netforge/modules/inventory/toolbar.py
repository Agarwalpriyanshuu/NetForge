from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from netforge.ui.components.primary_button import PrimaryButton


class InventoryToolbar(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        self.new_btn = PrimaryButton("➕ New Device")

        self.edit_btn = QPushButton("✏ Edit")

        self.delete_btn = QPushButton("🗑 Delete")

        self.refresh_btn = QPushButton("⟳ Refresh")

        self.search = QLineEdit()

        self.search.setPlaceholderText("Search inventory...")

        layout.addWidget(self.new_btn)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.refresh_btn)

        layout.addStretch()

        layout.addWidget(self.search)
