from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class PrimaryButton(QPushButton):

    def __init__(self, text):
        super().__init__(text)

        self.setProperty("class", "primary")
        self.setCursor(Qt.CursorShape.PointingHandCursor)