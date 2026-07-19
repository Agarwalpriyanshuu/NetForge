"""
Persistent, timestamped logging of SSH session output.

Every logged session gets its own plain-text file under NetForge's
application data directory, named for the host and start time. This
exists specifically for troubleshooting: being able to go back after
the fact and see exactly what a `tail -f`, `journalctl -f`, or
`tcpdump` session showed, correlated against wall-clock time.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import TextIO

from PySide6.QtCore import QStandardPaths

# ANSI CSI sequences, OSC sequences (title-setting, etc.), and single
# character-set-select escapes -- stripped so the on-disk log reads
# as plain text rather than being full of escape codes.
_ANSI_ESCAPE_RE = re.compile(
    rb"\x1b\[[0-9;?]*[a-zA-Z]"
    rb"|\x1b\][^\x07]*\x07"
    rb"|\x1b[()][AB012]"
)

# Insert a timestamp marker at least this often while data is
# actively streaming, so a long-running `tail -f`/`tcpdump` capture
# can still be correlated against wall-clock time.
_TIMESTAMP_MARKER_INTERVAL_BYTES = 16384


def logs_directory() -> Path:
    """
    The directory session logs are written to: the platform's
    standard application-data location for NetForge, under a
    ``session_logs`` subfolder, created on first use.
    """
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )

    if not base:
        base = str(Path.home() / ".netforge")

    path = Path(base) / "session_logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_log_filename(host: str, username: str) -> str:
    safe_host = re.sub(r"[^A-Za-z0-9_.-]", "_", host or "unknown-host")
    safe_user = re.sub(r"[^A-Za-z0-9_.-]", "_", username or "unknown-user")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_host}_{safe_user}_{timestamp}.log"


class SessionLogger:
    """
    Writes a single SSH session's output to a timestamped log file,
    stripping ANSI escape sequences and inserting periodic and
    event-driven timestamp markers.
    """

    def __init__(
        self,
        host: str,
        username: str,
        directory: Path | None = None,
    ) -> None:
        self.directory = directory or logs_directory()
        self.filename = build_log_filename(host, username)
        self.path = self.directory / self.filename

        self._file: TextIO | None = None
        self._bytes_since_marker = 0

    @property
    def is_active(self) -> bool:
        return self._file is not None

    def start(self) -> Path:
        """Open the log file for appending. Safe to call if already open."""
        if self._file is None:
            self._file = open(self.path, "a", encoding="utf-8", errors="replace")
            self.mark("Session log started")

        return self.path

    def stop(self) -> None:
        """Close the log file, if open."""
        if self._file is None:
            return

        self.mark("Session log stopped")
        self._file.close()
        self._file = None

    def write(self, data: bytes) -> None:
        """Append a chunk of raw terminal output to the log."""
        if self._file is None:
            return

        cleaned = _ANSI_ESCAPE_RE.sub(b"", data)
        text = cleaned.decode("utf-8", errors="replace")

        self._file.write(text)
        self._file.flush()

        self._bytes_since_marker += len(data)
        if self._bytes_since_marker >= _TIMESTAMP_MARKER_INTERVAL_BYTES:
            self.mark()
            self._bytes_since_marker = 0

    def mark(self, label: str | None = None) -> None:
        """Write a wall-clock timestamp marker line into the log."""
        if self._file is None:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        suffix = f" -- {label}" if label else ""
        self._file.write(f"\n[NetForge {timestamp}]{suffix}\n")
        self._file.flush()
