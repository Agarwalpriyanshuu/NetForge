"""
Manual "Quick Connect" dialog for opening an SSH session without
going through a saved Inventory entry.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from netforge.core.terminal.worker import HostKeyPolicy


class SSHConnectDialog(QDialog):
    """Collects connection parameters for an ad hoc SSH session."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Quick Connect")
        self.resize(420, 380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.host = QLineEdit()
        self.host.setPlaceholderText("hostname or IP address")

        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(22)

        self.username = QLineEdit()

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        key_row = QHBoxLayout()
        self.key_filename = QLineEdit()
        self.key_filename.setPlaceholderText("optional: path to private key")
        self.browse_key_btn = QPushButton("Browse…")
        key_row.addWidget(self.key_filename)
        key_row.addWidget(self.browse_key_btn)

        self.passphrase = QLineEdit()
        self.passphrase.setEchoMode(QLineEdit.EchoMode.Password)
        self.passphrase.setPlaceholderText("optional: key passphrase")

        self.host_key_policy = QComboBox()
        self.host_key_policy.addItem("Auto-accept new host keys", HostKeyPolicy.AUTO_ADD)
        self.host_key_policy.addItem("Reject unknown host keys", HostKeyPolicy.REJECT_UNKNOWN)

        self.timeout = QSpinBox()
        self.timeout.setRange(1, 120)
        self.timeout.setValue(10)
        self.timeout.setSuffix(" s")

        form.addRow("Host", self.host)
        form.addRow("Port", self.port)
        form.addRow("Username", self.username)
        form.addRow("Password", self.password)
        form.addRow("Private Key", key_row)
        form.addRow("Key Passphrase", self.passphrase)
        form.addRow("Host Key Policy", self.host_key_policy)
        form.addRow("Timeout", self.timeout)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.cancel_btn = QPushButton("Cancel")
        buttons.addStretch()
        buttons.addWidget(self.connect_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

        self.browse_key_btn.clicked.connect(self._browse_key_file)
        self.connect_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def _browse_key_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Private Key")
        if path:
            self.key_filename.setText(path)

    def get_data(self) -> dict:
        return {
            "host": self.host.text().strip(),
            "port": self.port.value(),
            "username": self.username.text().strip(),
            "password": self.password.text() or None,
            "key_filename": self.key_filename.text().strip() or None,
            "passphrase": self.passphrase.text() or None,
            "host_key_policy": self.host_key_policy.currentData(),
            "timeout": float(self.timeout.value()),
        }
