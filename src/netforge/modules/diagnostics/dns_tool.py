"""
DNS Lookup tool: forward lookups across common record types (A,
AAAA, MX, TXT, NS, CNAME) plus reverse (PTR) lookups, using
dnspython so real record data is available -- not just the single
A-record resolution the standard library's socket module gives you.
"""

from __future__ import annotations

import threading

import dns.exception
import dns.resolver
import dns.reversename
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from netforge.modules.diagnostics.output_view import DiagnosticOutput
from netforge.ui.components.primary_button import PrimaryButton

_FORWARD_RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "NS", "CNAME"]
_LOOKUP_TIMEOUT_SECONDS = 5.0


class DnsLookupWorker(QThread):
    """
    Runs one or more DNS queries on a background thread. Each
    individual query is bounded by ``_LOOKUP_TIMEOUT_SECONDS``, which
    also caps how long a Stop request takes to actually take effect
    -- dnspython's resolver call is synchronous and cannot be
    interrupted mid-flight, so "stop" here means "don't start the
    next query", not "abort the in-flight syscall".
    """

    result = Signal(str, list)  # record_type, [answer strings]
    lookup_error = Signal(str, str)  # record_type, message
    finished_all = Signal()

    def __init__(self, target: str, record_types: list[str], reverse: bool, parent=None) -> None:
        super().__init__(parent)
        self.target = target
        self.record_types = record_types
        self.reverse = reverse
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        resolver = dns.resolver.Resolver()

        if self.reverse:
            self._run_reverse(resolver)
        else:
            self._run_forward(resolver)

        self.finished_all.emit()

    def _run_forward(self, resolver: dns.resolver.Resolver) -> None:
        for record_type in self.record_types:
            if self._stop_event.is_set():
                return

            try:
                answers = resolver.resolve(
                    self.target, record_type, lifetime=_LOOKUP_TIMEOUT_SECONDS
                )
                self.result.emit(record_type, [a.to_text() for a in answers])
            except dns.resolver.NXDOMAIN:
                self.lookup_error.emit(
                    record_type, f"{self.target} does not exist (NXDOMAIN)."
                )
                return
            except dns.resolver.NoAnswer:
                self.lookup_error.emit(record_type, "No records of this type.")
            except dns.exception.DNSException as exc:
                self.lookup_error.emit(record_type, str(exc))

    def _run_reverse(self, resolver: dns.resolver.Resolver) -> None:
        try:
            reverse_name = dns.reversename.from_address(self.target)
        except dns.exception.SyntaxError:
            self.lookup_error.emit("PTR", f"{self.target!r} is not a valid IP address.")
            return

        try:
            answers = resolver.resolve(
                reverse_name, "PTR", lifetime=_LOOKUP_TIMEOUT_SECONDS
            )
            self.result.emit("PTR", [a.to_text() for a in answers])
        except dns.resolver.NXDOMAIN:
            self.lookup_error.emit("PTR", "No PTR record found (NXDOMAIN).")
        except dns.resolver.NoAnswer:
            self.lookup_error.emit("PTR", "No PTR record for this address.")
        except dns.exception.DNSException as exc:
            self.lookup_error.emit("PTR", str(exc))


class DnsLookupPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._worker: DnsLookupWorker | None = None

        layout = QVBoxLayout(self)

        form_row = QHBoxLayout()

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Hostname (or IP address for reverse lookup)")
        self.target_input.returnPressed.connect(self._on_run_clicked)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Forward Lookup (all common types)", "forward")
        self.mode_combo.addItem("Reverse Lookup (PTR)", "reverse")

        self.run_btn = PrimaryButton("▶ Lookup")
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setEnabled(False)

        form_row.addWidget(QLabel("Target:"))
        form_row.addWidget(self.target_input, 1)
        form_row.addWidget(self.mode_combo)
        form_row.addWidget(self.run_btn)
        form_row.addWidget(self.stop_btn)

        self.output = DiagnosticOutput()

        layout.addLayout(form_row)
        layout.addWidget(self.output, 1)

        self.run_btn.clicked.connect(self._on_run_clicked)
        self.stop_btn.clicked.connect(self._on_stop_clicked)

    def _on_run_clicked(self) -> None:
        target = self.target_input.text().strip()

        if not target:
            self.output.append_line("Enter a hostname or IP address first.", "error")
            return

        if self._worker is not None and self._worker.isRunning():
            return

        reverse = self.mode_combo.currentData() == "reverse"

        self.output.clear_output()
        self.output.append_line(
            f"Resolving {target} ({'reverse' if reverse else 'forward'})...", "info"
        )

        self._worker = DnsLookupWorker(target, _FORWARD_RECORD_TYPES, reverse)
        self._worker.result.connect(self._on_result)
        self._worker.lookup_error.connect(self._on_lookup_error)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _on_stop_clicked(self) -> None:
        if self._worker is not None:
            self._worker.stop()

    def _on_result(self, record_type: str, answers: list[str]) -> None:
        self.output.append_line(f"{record_type:<6} {len(answers)} record(s):", "success")
        for answer in answers:
            self.output.append_line(f"    {answer}")

    def _on_lookup_error(self, record_type: str, message: str) -> None:
        self.output.append_line(f"{record_type:<6} {message}", "muted")

    def _on_finished(self) -> None:
        self.output.append_line("-- lookup finished --", "info")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._worker = None

    def cleanup(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(int(_LOOKUP_TIMEOUT_SECONDS * 1000) + 500)
