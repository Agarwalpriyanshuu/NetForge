from PySide6.QtWidgets import QLabel, QStatusBar


class NetForgeStatusBar(QStatusBar):
    def __init__(self):
        super().__init__()

        self.setObjectName("netforgeStatusBar")

        self.showMessage("Ready")

        version = QLabel("NetForge v0.0.1")

        self.addPermanentWidget(version)