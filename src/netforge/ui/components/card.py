from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)


class Card(QFrame):

    def __init__(self, title):
        super().__init__()

        self.setMinimumHeight(120)

        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)

        label = QLabel(title)

        label.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()