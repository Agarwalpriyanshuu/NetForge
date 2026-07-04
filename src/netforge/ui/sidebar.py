from PySide6.QtWidgets import QListWidget


class Sidebar(QListWidget):

    def __init__(self):
        super().__init__()

        self.setFixedWidth(230)

    def load_items(self, items):

        self.clear()

        self.addItems(items)