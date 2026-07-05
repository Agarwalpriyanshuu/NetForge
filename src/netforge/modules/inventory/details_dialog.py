from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)


class ConnectionDetailsDialog(QDialog):

    def __init__(self, connection):
        super().__init__()

        self.connection = connection

        self.setWindowTitle("Connection Details")
        self.resize(500, 450)

        main_layout = QVBoxLayout(self)

        form = QFormLayout()

        form.addRow("Connection Name", QLabel(connection.name))
        form.addRow("Hostname", QLabel(connection.hostname))
        form.addRow("IP Address", QLabel(connection.ip_address))
        form.addRow("Username", QLabel(connection.username))
        form.addRow("Protocol", QLabel(connection.protocol))
        form.addRow("Port", QLabel(str(connection.port)))

        notes = QLabel(connection.notes if connection.notes else "-")
        notes.setWordWrap(True)

        form.addRow("Notes", notes)

        main_layout.addLayout(form)

        button_layout = QHBoxLayout()

        self.ssh_btn = QPushButton("SSH")
        self.ping_btn = QPushButton("Ping")
        self.browser_btn = QPushButton("Browser")

        button_layout.addWidget(self.ssh_btn)
        button_layout.addWidget(self.ping_btn)
        button_layout.addWidget(self.browser_btn)

        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        bottom_layout = QHBoxLayout()

        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.close_btn = QPushButton("Close")

        bottom_layout.addStretch()

        bottom_layout.addWidget(self.edit_btn)
        bottom_layout.addWidget(self.delete_btn)
        bottom_layout.addWidget(self.close_btn)

        main_layout.addLayout(bottom_layout)

        self.close_btn.clicked.connect(self.close)

        self.ssh_btn.clicked.connect(self.not_implemented)
        self.ping_btn.clicked.connect(self.not_implemented)
        self.browser_btn.clicked.connect(self.not_implemented)
        self.edit_btn.clicked.connect(self.not_implemented)
        self.delete_btn.clicked.connect(self.not_implemented)

    def not_implemented(self):
        print("Feature not implemented yet.")