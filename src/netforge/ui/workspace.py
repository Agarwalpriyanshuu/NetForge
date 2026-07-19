from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout


class Workspace(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel("Dashboard")

        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)