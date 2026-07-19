"""
Reusable terminal emulation framework for NetForge.

This package provides a Paramiko + pyte based terminal architecture
that is consumed by the SSH module (and, in the future, by any other
module that needs an interactive remote or local shell: Telnet,
Serial Console, local shell tabs, etc).

Architecture:

    Inventory
        -> SSHController
            -> SSHSession (core.terminal.session)
                -> SSHWorker (core.terminal.worker)   [QThread]
                    -> paramiko.Channel (invoke_shell PTY)
                -> TerminalEmulator (core.terminal.emulator) [pyte]
            -> TerminalRenderer (core.terminal.renderer)      [QWidget]

Nothing in this package knows about SSH specifically except
``session.py``, which orchestrates a worker + emulator pair. The
renderer, emulator, keyboard, clipboard, colors and cursor modules
are fully protocol-agnostic and can be reused by any future module
that needs to display and drive a terminal.
"""

from netforge.core.terminal.session import SSHSession, SessionState
from netforge.core.terminal.emulator import TerminalEmulator
from netforge.core.terminal.renderer import TerminalRenderer

__all__ = [
    "SSHSession",
    "SessionState",
    "TerminalEmulator",
    "TerminalRenderer",
]
