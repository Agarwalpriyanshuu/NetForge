"""
Ping tool: wraps the OS ping binary and streams output live.
"""

from __future__ import annotations

import platform

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from netforge.core.diagnostics.process_worker import ProcessStreamWorker
from netforge.modules.diagnostics.output_view import DiagnosticOutput
from netforge.ui.components.primary_button import PrimaryButton


def build_ping_command(host: str, count: int, continuous: bool) -> list[str]:
    if platform.system() == "Windows":
        if continuous:
            return ["ping", "-t", host]
        return ["ping", "-n", str(count), host]

    if continuous:
        return ["ping", host]
    return ["ping", "-c", str(count), host]


class PingPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._worker: ProcessStreamWorker | None = None

        layout = QVBoxLayout(self)

        form_row = QHBoxLayout()

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Hostname or IP address")
        self.host_input.returnPressed.connect(self._on_run_clicked)

        self.count_input = QSpinBox()
        self.count_input.setRange(1, 999)
        self.count_input.setValue(4)
        self.count_input.setPrefix("Count: ")

        self.continuous_checkbox = QCheckBox("Continuous")
        self.continuous_checkbox.toggled.connect(
            lambda checked: self.count_input.setDisabled(checked)
        )

        self.run_btn = PrimaryButton("▶ Ping")
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setEnabled(False)

        form_row.addWidget(QLabel("Host:"))
        form_row.addWidget(self.host_input, 1)
        form_row.addWidget(self.count_input)
        form_row.addWidget(self.continuous_checkbox)
        form_row.addWidget(self.run_btn)
        form_row.addWidget(self.stop_btn)

        self.output = DiagnosticOutput()

        layout.addLayout(form_row)
        layout.addWidget(self.output, 1)

        self.run_btn.clicked.connect(self._on_run_clicked)
        self.stop_btn.clicked.connect(self._on_stop_clicked)

    def _on_run_clicked(self) -> None:
        host = self.host_input.text().strip()

        if not host:
            self.output.append_line("Enter a hostname or IP address first.", "error")
            return

        if self._worker is not None and self._worker.isRunning():
            return

        self.output.clear_output()
        self.output.append_line(f"Pinging {host}...", "info")

        args = build_ping_command(
            host, self.count_input.value(), self.continuous_checkbox.isChecked()
        )

        self._worker = ProcessStreamWorker(args)
        self._worker.line_received.connect(self.output.append_line)
        self._worker.finished_run.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _on_stop_clicked(self) -> None:
        if self._worker is not None:
            self._worker.stop()

    def _on_finished(self, exit_code: int) -> None:
        if exit_code == 0:
            self.output.append_line("-- ping finished --", "success")
        elif exit_code == -1:
            self.output.append_line("-- stopped --", "muted")
        else:
            self.output.append_line(f"-- ping exited with code {exit_code} --", "error")

        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._worker = None

    def _on_error(self, message: str) -> None:
        self.output.append_line(message, "error")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._worker = None

    def cleanup(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(2000)
