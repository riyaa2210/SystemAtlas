"""
Password hashing utilities using bcrypt directly.
We call bcrypt directly rather than through passlib since passlib 1.7.4
has a known calibration hang with bcrypt >= 4.x.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password. Returns a string suitable for DB storage."""
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False
