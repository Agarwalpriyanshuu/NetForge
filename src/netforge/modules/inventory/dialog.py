from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
)


class InventoryDialog(QDialog):

    def __init__(self, data=None):
        super().__init__()

        self.setWindowTitle("New Connection")
        self.resize(500, 500)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name = QLineEdit()
        self.hostname = QLineEdit()
        self.ip = QLineEdit()
        self.username = QLineEdit()

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        self.protocol = QComboBox()
        self.protocol.addItems([
            "SSH",
            "RDP",
            "HTTPS",
            "HTTP",
            "Telnet"
        ])

        self.port = QLineEdit("22")

        self.notes = QTextEdit()

        form.addRow("Connection Name", self.name)
        form.addRow("Hostname / FQDN", self.hostname)
        form.addRow("IP Address", self.ip)
        form.addRow("Username", self.username)
        form.addRow("Password", self.password)
        form.addRow("Protocol", self.protocol)
        form.addRow("Port", self.port)
        form.addRow("Notes", self.notes)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")

        buttons.addStretch()
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)

        layout.addLayout(buttons)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        if data:

            self.name.setText(data.name)
            self.hostname.setText(data.hostname)
            self.ip.setText(data.ip_address)
            self.username.setText(data.username)
            self.password.setText(data.password)
            self.protocol.setCurrentText(data.protocol)
            self.port.setText(str(data.port))
            self.notes.setPlainText(data.notes)

    def get_data(self):

        return {
            "name": self.name.text(),
            "hostname": self.hostname.text(),
            "ip": self.ip.text(),
            "username": self.username.text(),
            "password": self.password.text(),
            "protocol": self.protocol.currentText(),
            "port": self.port.text(),
            "notes": self.notes.toPlainText(),
        }