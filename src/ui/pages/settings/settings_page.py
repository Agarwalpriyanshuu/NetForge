from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class SettingsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel("Settings")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)