"""Bcrypt only accepts the first 72 bytes of a password; passlib raises if the input is longer."""


def normalize_password_for_bcrypt(password: str) -> str:
    """
    Return a string whose UTF-8 encoding is at most 72 bytes, without splitting a multibyte character.
    """
    if not password:
        return password
    data = password.encode("utf-8")
    if len(data) <= 72:
        return password
    data = data[:72]
    while data:
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            data = data[:-1]
    return ""
