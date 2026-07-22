"""
Reusable background worker that runs a system command (ping,
traceroute/tracert, etc.) and streams its output line by line.

This deliberately wraps the OS's own ping/traceroute binaries rather
than reimplementing raw ICMP sockets: raw sockets need elevated
privileges on most platforms, while the system binaries are always
available, already handle platform quirks correctly, and are exactly
what a network engineer would run by hand anyway -- NetForge is just
giving it a persistent, loggable, non-blocking home.
"""

from __future__ import annotations

import locale
import subprocess
import threading

from PySide6.QtCore import QThread, Signal


class ProcessStreamWorker(QThread):
    """
    Runs ``args`` as a subprocess on a background thread and emits
    each line of combined stdout/stderr as it arrives, so the UI can
    show live, streaming output without ever blocking.
    """

    line_received = Signal(str)
    finished_run = Signal(int)  # exit code
    error = Signal(str)

    def __init__(self, args: list[str], parent=None) -> None:
        super().__init__(parent)
        self.args = args

        self._process: subprocess.Popen | None = None
        self._stop_event = threading.Event()

    def run(self) -> None:
        creationflags = 0
        startupinfo = None

        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            # Prevent a console window from flashing up on Windows.
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            self._process = subprocess.Popen(
                self.args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=locale.getpreferredencoding(False),
                errors="replace",
                bufsize=1,
                creationflags=creationflags,
            )
        except FileNotFoundError:
            self.error.emit(
                f"Command not found: {self.args[0]!r}. Is it installed and on PATH?"
            )
            return
        except OSError as exc:
            self.error.emit(f"Failed to start process: {exc}")
            return

        assert self._process.stdout is not None

        try:
            for line in self._process.stdout:
                if self._stop_event.is_set():
                    break
                self.line_received.emit(line.rstrip("\r\n"))
        except (OSError, ValueError):
            pass

        if self._stop_event.is_set():
            self._terminate()
            self.finished_run.emit(-1)
            return

        return_code = self._process.wait()
        self.finished_run.emit(return_code)

    def stop(self) -> None:
        self._stop_event.set()
        self._terminate()

    def _terminate(self) -> None:
        if self._process is not None and self._process.poll() is None:
            try:
                self._process.terminate()
            except OSError:
                pass
