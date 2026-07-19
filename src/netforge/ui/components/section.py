from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)


class Section(QFrame):

    def __init__(self, title):
        super().__init__()

        self.setProperty("class", "section")

        self.layout = QVBoxLayout(self)

        heading = QLabel(title)

        heading.setStyleSheet("""
            font-size:16px;
            font-weight:bold;
        """)

        self.layout.addWidget(heading)