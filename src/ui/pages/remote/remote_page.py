from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class RemotePage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel("Remote Manager")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)