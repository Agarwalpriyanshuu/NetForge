from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class SSHPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel("SSH Manager")

        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)