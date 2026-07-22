"""
Encrypts and decrypts credentials (currently: the Inventory
Connection password field) before they touch the SQLite database.

This protects the data *at rest* -- if someone copies
``netforge.db`` off the machine, the passwords inside it are useless
without the separate key file, which lives outside the repo/database
in NetForge's application-data directory. It does **not** protect
against someone with access to the running application or to the
same user account on the same machine: the key is stored locally,
unencrypted, and readable by that OS user. That is a reasonable,
honest middle ground for a desktop network tool, not enterprise-grade
key management -- if NetForge ever needs to defend against a
compromised local account, this needs to move to an OS keychain
(Windows Credential Manager, macOS Keychain, etc.) instead.
"""

from __future__ import annotations

import threading
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from loguru import logger
from PySide6.QtCore import QStandardPaths

# Values encrypted by this module are stored with this prefix so
# decrypt() can tell an encrypted value apart from a legacy plaintext
# password saved before this feature existed, and handle both
# transparently rather than corrupting old data.
_PREFIX = "fernet:"

_lock = threading.Lock()
_fernet: Fernet | None = None


def _key_file_path() -> Path:
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )

    if not base:
        base = str(Path.home() / ".netforge")

    directory = Path(base)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "credentials.key"


def _load_or_create_key() -> bytes:
    path = _key_file_path()

    if path.exists():
        return path.read_bytes()

    key = Fernet.generate_key()
    path.write_bytes(key)

    try:
        path.chmod(0o600)
    except OSError:
        # Not all platforms/filesystems support POSIX permission bits
        # (notably Windows) -- best effort only.
        pass

    return key


def _get_fernet() -> Fernet:
    global _fernet

    with _lock:
        if _fernet is None:
            _fernet = Fernet(_load_or_create_key())
        return _fernet


def encrypt(plaintext: str | None) -> str:
    """Encrypt a value for storage. Empty input returns empty output."""
    if not plaintext:
        return ""

    token = _get_fernet().encrypt(plaintext.encode("utf-8"))
    return _PREFIX + token.decode("ascii")


def decrypt(stored_value: str | None) -> str:
    """
    Decrypt a value read from storage.

    Values without the encryption prefix are assumed to be legacy
    plaintext from before this feature existed, and are returned
    unchanged -- they will be transparently re-encrypted the next
    time the record is saved.
    """
    if not stored_value:
        return ""

    if not stored_value.startswith(_PREFIX):
        return stored_value

    token = stored_value[len(_PREFIX):]

    try:
        return _get_fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        logger.warning(
            "Could not decrypt a stored credential (invalid token or key "
            "mismatch); treating it as empty rather than failing."
        )
        return ""
