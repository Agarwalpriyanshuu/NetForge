"""
Background thread that owns the actual Paramiko connection and PTY
channel for a single SSH session.

This is the only piece of the terminal framework that is allowed to
perform blocking network I/O. It never touches the UI directly --
all communication with the rest of the application happens through
:class:`~netforge.core.terminal.signals.WorkerSignals`, which Qt
delivers safely across the thread boundary.
"""

from __future__ import annotations

import queue
import select
import socket
import threading

import paramiko
from PySide6.QtCore import QThread

from netforge.core.terminal.signals import WorkerSignals

# How long select() blocks per loop iteration while waiting for
# incoming data or a stop request. Small enough to keep the worker
# responsive to stop()/write() calls, large enough to avoid busy-looping.
_POLL_INTERVAL = 0.2

# Size of each recv() call against the channel.
_RECV_CHUNK_SIZE = 32768


class HostKeyPolicy:
    """Supported host key verification strategies."""

    AUTO_ADD = "auto_add"
    REJECT_UNKNOWN = "reject_unknown"


class SSHWorker(QThread):
    """
    Owns a single Paramiko SSH connection and interactive shell
    channel, running entirely on a background Qt thread.

    :param host: hostname or IP address to connect to.
    :param port: TCP port to connect to.
    :param username: SSH username.
    :param password: SSH password. Ignored if ``key_filename`` is set.
    :param key_filename: path to a private key file, for key-based auth.
    :param passphrase: passphrase for the private key, if any.
    :param timeout: socket/banner/auth timeout, in seconds.
    :param term: terminal type advertised to the remote (``$TERM``).
    :param cols: initial terminal width, in character columns.
    :param rows: initial terminal height, in character rows.
    :param host_key_policy: one of :class:`HostKeyPolicy`.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str | None = None,
        key_filename: str | None = None,
        passphrase: str | None = None,
        timeout: float = 10.0,
        term: str = "xterm-256color",
        cols: int = 80,
        rows: int = 24,
        host_key_policy: str = HostKeyPolicy.AUTO_ADD,
    ) -> None:
        super().__init__()
        self.setObjectName(f"SSHWorker-{host}")

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.passphrase = passphrase
        self.timeout = timeout
        self.term = term
        self.cols = cols
        self.rows = rows
        self.host_key_policy = host_key_policy

        self.signals = WorkerSignals()

        self._client: paramiko.SSHClient | None = None
        self._channel: paramiko.Channel | None = None

        self._outgoing: "queue.Queue[bytes]" = queue.Queue()
        self._stop_event = threading.Event()
        self._channel_lock = threading.Lock()

        self._connected = False

    # ------------------------------------------------------------------
    # Public, thread-safe API. These are the only methods that should be
    # called from the UI/main thread while the worker is running.
    # ------------------------------------------------------------------

    def send(self, data: bytes) -> None:
        """Queue bytes to be written to the remote PTY."""
        if not data:
            return
        self._outgoing.put(data)

    def resize(self, cols: int, rows: int) -> None:
        """Resize the remote PTY to match the widget's new dimensions."""
        self.cols = cols
        self.rows = rows

        with self._channel_lock:
            channel = self._channel
            if channel is not None and self._connected:
                try:
                    channel.resize_pty(width=cols, height=rows)
                except (paramiko.SSHException, OSError):
                    # The channel may already be closing; resize failures
                    # here are not fatal, the next reconnect will pick up
                    # the correct size.
                    pass

    def stop(self) -> None:
        """
        Request a graceful shutdown of the worker.

        This unblocks the background ``run()`` loop (by closing the
        channel/socket, which causes ``select()`` to return) and marks
        the worker as stopping so it exits its loop and closes cleanly.
        """
        self._stop_event.set()

        with self._channel_lock:
            if self._channel is not None:
                try:
                    self._channel.close()
                except Exception:
                    pass

            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    pass

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # Thread entry point.
    # ------------------------------------------------------------------

    def run(self) -> None:
        try:
            self._client = self._build_client()
            self._connect_client(self._client)
        except paramiko.AuthenticationException as exc:
            self.signals.error.emit("auth", str(exc) or "Authentication failed.")
            return
        except paramiko.BadHostKeyException as exc:
            self.signals.error.emit("host_key", str(exc))
            return
        except socket.timeout:
            self.signals.error.emit(
                "timeout",
                f"Connection to {self.host}:{self.port} timed out.",
            )
            return
        except ConnectionRefusedError:
            self.signals.error.emit(
                "refused",
                f"Connection to {self.host}:{self.port} was refused.",
            )
            return
        except (socket.gaierror, OSError) as exc:
            self.signals.error.emit(
                "unreachable",
                f"Host {self.host} is unreachable: {exc}",
            )
            return
        except paramiko.SSHException as exc:
            self.signals.error.emit("unknown", str(exc))
            return

        try:
            channel = self._client.invoke_shell(
                term=self.term,
                width=self.cols,
                height=self.rows,
            )
            channel.settimeout(0.0)
        except paramiko.SSHException as exc:
            self.signals.error.emit("unknown", f"Failed to open shell: {exc}")
            self._safe_close()
            return

        with self._channel_lock:
            self._channel = channel

        self._connected = True
        self.signals.connected.emit()

        try:
            self._io_loop(channel)
        finally:
            self._connected = False
            self._safe_close()

    # ------------------------------------------------------------------
    # Internal helpers.
    # ------------------------------------------------------------------

    def _build_client(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.load_system_host_keys()

        if self.host_key_policy == HostKeyPolicy.REJECT_UNKNOWN:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        return client

    def _connect_client(self, client: paramiko.SSHClient) -> None:
        connect_kwargs = dict(
            hostname=self.host,
            port=self.port,
            username=self.username,
            timeout=self.timeout,
            banner_timeout=self.timeout,
            auth_timeout=self.timeout,
            allow_agent=self.key_filename is None,
            look_for_keys=self.key_filename is None,
        )

        if self.key_filename:
            connect_kwargs["key_filename"] = self.key_filename
            connect_kwargs["passphrase"] = self.passphrase
        else:
            connect_kwargs["password"] = self.password

        client.connect(**connect_kwargs)

    def _io_loop(self, channel: paramiko.Channel) -> None:
        """
        Main read/write loop for the lifetime of the shell channel.

        Uses ``select()`` so we never block indefinitely: each pass we
        check for incoming data, check for a stop request, and flush
        any queued outgoing writes.
        """
        while not self._stop_event.is_set():
            try:
                readable, _, _ = select.select(
                    [channel], [], [], _POLL_INTERVAL
                )
            except (OSError, ValueError):
                # Channel's underlying socket was closed from under us.
                break

            if channel.closed:
                self.signals.disconnected.emit("Connection closed by remote host.")
                break

            if readable:
                try:
                    if channel.recv_ready():
                        data = channel.recv(_RECV_CHUNK_SIZE)
                        if not data:
                            self.signals.disconnected.emit(
                                "Connection closed by remote host."
                            )
                            break
                        self.signals.data_received.emit(data)
                except (OSError, EOFError) as exc:
                    self.signals.disconnected.emit(f"Connection lost: {exc}")
                    break

            self._flush_outgoing(channel)

            if channel.exit_status_ready():
                self.signals.disconnected.emit("Remote shell exited.")
                break

        if self._stop_event.is_set():
            self.signals.disconnected.emit("Disconnected.")

    def _flush_outgoing(self, channel: paramiko.Channel) -> None:
        while True:
            try:
                data = self._outgoing.get_nowait()
            except queue.Empty:
                return

            try:
                channel.sendall(data)
            except (OSError, paramiko.SSHException) as exc:
                self.signals.disconnected.emit(f"Write failed: {exc}")
                return

    def _safe_close(self) -> None:
        with self._channel_lock:
            if self._channel is not None:
                try:
                    self._channel.close()
                except Exception:
                    pass
                self._channel = None

            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    pass
