from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGridLayout,
)

from ui.components.card import Card
from ui.components.section import Section


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")

        main_layout.addWidget(title)

        quick_launch = Section("Quick Launch")

        grid = QGridLayout()

        grid.addWidget(Card("SSH Manager"), 0, 0)
        grid.addWidget(Card("Network Tools"), 0, 1)
        grid.addWidget(Card("Packet Lab"), 1, 0)
        grid.addWidget(Card("Utilities"), 1, 1)

        quick_launch.layout.addLayout(grid)

        main_layout.addWidget(quick_launch)

        recent = Section("Recent Sessions")

        recent.layout.addWidget(
            QLabel("No recent sessions.")
        )

        main_layout.addWidget(recent)

        status = Section("System Status")

        status.layout.addWidget(
            QLabel("NetForge is ready.")
        )

        main_layout.addWidget(status)

        main_layout.addStretch()