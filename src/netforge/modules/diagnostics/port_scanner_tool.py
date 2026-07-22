"""
Port Scanner tool: concurrent TCP connect scan against a host.

This is a connect() scan (not a raw SYN scan) so it needs no elevated
privileges on any platform -- exactly the tradeoff a GUI troubleshooting
tool wants: works everywhere, out of the box, no admin prompt.
"""

from __future__ import annotations

import concurrent.futures
import socket
import threading

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from netforge.ui.components.primary_button import PrimaryButton

# Hard ceiling on how many ports a single scan can request, so a typo
# like "1-65535" with a low timeout can't accidentally hammer a host
# with tens of thousands of concurrent connection attempts.
_MAX_PORTS_PER_SCAN = 5000

_COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 123, 135, 139, 143, 161, 179,
    389, 443, 445, 465, 514, 587, 636, 993, 995, 1433, 1521, 2049,
    3306, 3389, 5432, 5900, 5985, 6379, 8080, 8443, 9200, 27017,
]


def parse_port_spec(spec: str) -> list[int]:
    """
    Parse a port specification like ``"22,80,443"`` or ``"1-1024"``
    (or a mix, comma-separated) into a sorted, de-duplicated list of
    port numbers.

    Raises ``ValueError`` with a human-readable message on anything
    malformed or out of range.
    """
    ports: set[int] = set()

    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue

        if "-" in chunk:
            start_str, _, end_str = chunk.partition("-")
            try:
                start, end = int(start_str), int(end_str)
            except ValueError:
                raise ValueError(f"Invalid port range: {chunk!r}")
            if start > end:
                raise ValueError(f"Invalid port range: {chunk!r} (start > end)")
            ports.update(range(start, end + 1))
        else:
            try:
                ports.add(int(chunk))
            except ValueError:
                raise ValueError(f"Invalid port: {chunk!r}")

    for port in ports:
        if not (1 <= port <= 65535):
            raise ValueError(f"Port {port} is out of range (1-65535).")

    if not ports:
        raise ValueError("No ports specified.")

    if len(ports) > _MAX_PORTS_PER_SCAN:
        raise ValueError(
            f"{len(ports)} ports requested; a single scan is capped at "
            f"{_MAX_PORTS_PER_SCAN} to avoid overwhelming the target."
        )

    return sorted(ports)


def guess_service(port: int) -> str:
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return ""


class PortScannerWorker(QThread):
    port_result = Signal(int, bool, str)  # port, is_open, service_guess
    progress = Signal(int, int)  # completed, total
    finished_scan = Signal()

    def __init__(
        self,
        host: str,
        ports: list[int],
        timeout: float = 1.0,
        max_workers: int = 100,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.host = host
        self.ports = ports
        self.timeout = timeout
        self.max_workers = max_workers
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        total = len(self.ports)
        completed = 0

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        future_to_port = {
            executor.submit(self._scan_port, port): port for port in self.ports
        }

        try:
            for future in concurrent.futures.as_completed(future_to_port):
                if self._stop_event.is_set():
                    break

                port = future_to_port[future]
                try:
                    is_open = future.result()
                except Exception:
                    is_open = False

                completed += 1
                service = guess_service(port) if is_open else ""
                self.port_result.emit(port, is_open, service)
                self.progress.emit(completed, total)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        self.finished_scan.emit()

    def _scan_port(self, port: int) -> bool:
        try:
            with socket.create_connection((self.host, port), timeout=self.timeout):
                return True
        except (OSError, socket.timeout):
            return False


class PortScannerPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._worker: PortScannerWorker | None = None

        layout = QVBoxLayout(self)

        form_row = QHBoxLayout()

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Hostname or IP address")
        self.host_input.returnPressed.connect(self._on_run_clicked)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Common Ports", "common")
        self.preset_combo.addItem("Well-Known (1-1024)", "wellknown")
        self.preset_combo.addItem("Custom", "custom")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        self.ports_input = QLineEdit()
        self.ports_input.setPlaceholderText("e.g. 22,80,443 or 1-1024")
        self.ports_input.setText(",".join(str(p) for p in _COMMON_PORTS))

        self.timeout_input = QDoubleSpinBox()
        self.timeout_input.setRange(0.1, 10.0)
        self.timeout_input.setSingleStep(0.1)
        self.timeout_input.setValue(1.0)
        self.timeout_input.setSuffix(" s")
        self.timeout_input.setPrefix("Timeout: ")

        self.run_btn = PrimaryButton("▶ Scan")
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setEnabled(False)

        form_row.addWidget(QLabel("Host:"))
        form_row.addWidget(self.host_input, 1)
        form_row.addWidget(self.preset_combo)
        form_row.addWidget(self.ports_input, 1)
        form_row.addWidget(self.timeout_input)
        form_row.addWidget(self.run_btn)
        form_row.addWidget(self.stop_btn)

        self.status_label = QLabel("Ready.")

        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Port", "Status", "Service"])
        self.results_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSortingEnabled(True)

        layout.addLayout(form_row)
        layout.addWidget(self.status_label)
        layout.addWidget(self.results_table, 1)

        self.run_btn.clicked.connect(self._on_run_clicked)
        self.stop_btn.clicked.connect(self._on_stop_clicked)

    def _on_preset_changed(self) -> None:
        preset = self.preset_combo.currentData()

        if preset == "common":
            self.ports_input.setText(",".join(str(p) for p in _COMMON_PORTS))
            self.ports_input.setReadOnly(True)
        elif preset == "wellknown":
            self.ports_input.setText("1-1024")
            self.ports_input.setReadOnly(True)
        else:
            self.ports_input.setReadOnly(False)

    def _on_run_clicked(self) -> None:
        host = self.host_input.text().strip()

        if not host:
            self.status_label.setText("Enter a hostname or IP address first.")
            return

        try:
            ports = parse_port_spec(self.ports_input.text())
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return

        if self._worker is not None and self._worker.isRunning():
            return

        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(0)
        self.results_table.setSortingEnabled(True)
        self.status_label.setText(f"Scanning {host} ({len(ports)} ports)...")

        self._worker = PortScannerWorker(
            host, ports, timeout=self.timeout_input.value()
        )
        self._worker.port_result.connect(self._on_port_result)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_scan.connect(self._on_finished)
        self._worker.start()

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _on_stop_clicked(self) -> None:
        if self._worker is not None:
            self._worker.stop()

    def _on_port_result(self, port: int, is_open: bool, service: str) -> None:
        if not is_open:
            return

        self.results_table.setSortingEnabled(False)
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)

        port_item = QTableWidgetItem()
        port_item.setData(0x0100, port)  # Qt.ItemDataRole.EditRole, for numeric sort
        port_item.setText(str(port))

        status_item = QTableWidgetItem("Open")
        service_item = QTableWidgetItem(service or "unknown")

        self.results_table.setItem(row, 0, port_item)
        self.results_table.setItem(row, 1, status_item)
        self.results_table.setItem(row, 2, service_item)
        self.results_table.setSortingEnabled(True)

    def _on_progress(self, completed: int, total: int) -> None:
        open_count = self.results_table.rowCount()
        self.status_label.setText(
            f"Scanning... {completed}/{total} checked, {open_count} open"
        )

    def _on_finished(self) -> None:
        open_count = self.results_table.rowCount()
        self.status_label.setText(f"Scan finished -- {open_count} open port(s) found.")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._worker = None

    def cleanup(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(2000)
