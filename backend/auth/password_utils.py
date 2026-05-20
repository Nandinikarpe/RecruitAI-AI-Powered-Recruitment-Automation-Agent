"""Bcrypt only accepts the first 72 bytes; passlib raises on longer secrets. We pre-hash so any UTF-8 password works."""

import hashlib


def normalize_password_for_bcrypt(password: str) -> str:
    """
    Map the password to a fixed-length ASCII string (64 chars) so bcrypt never sees >72 bytes.

    New accounts use this before hashing. verify_password also tries legacy raw-password hashes.
    """
    if not password:
        return password
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
