import hashlib
import hmac
import re
from typing import Any, Optional
from datetime import datetime, timedelta
import secrets
from app.core.config import settings


def sanitize_formula_injection(value: Any) -> Any:
    """
    Prevents CSV / Excel formula injection (CWE-1236).
    If a cell value starts with '=', '+', '-', '@', '\t', '\r', prefix with single quote `'`.
    """
    if value is None:
        return ""
    str_val = str(value)
    if not str_val:
        return ""
    # Characters dangerous at start of spreadsheet cell
    if str_val[0] in ("=", "+", "-", "@", "\t", "\r", "%", "|"):
        return "'" + str_val
    return str_val


def hash_token(token: str) -> str:
    """Generate SHA-256 hash of a token for secure storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_uuid_str() -> str:
    """Generate secure random UUID hex."""
    import uuid
    return str(uuid.uuid4())
