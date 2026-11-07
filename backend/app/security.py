import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt

from app.config import get_settings


def hash_secret(value: str) -> str:
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_secret(value: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def new_recovery_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    chunks = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3)]
    return "-".join(chunks)


def normalize_recovery_code(code: str) -> str:
    return code.strip().upper().replace("-", "").replace(" ", "")


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expiry() -> datetime:
    days = get_settings().session_days
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=days)
