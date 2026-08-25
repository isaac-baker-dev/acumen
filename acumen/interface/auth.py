"""Acumen Authentication - Secure password protection for web UI."""

import os
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv

load_dotenv(override=True)

SECRET_KEY = os.getenv("ACUMEN_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "acumen-default-secret-change-me":
    import secrets
    SECRET_KEY = secrets.token_hex(32)

ALGORITHM = os.getenv("ACUMEN_ALGORITHM", "HS256")
TOKEN_EXPIRE_HOURS = int(os.getenv("ACUMEN_TOKEN_EXPIRE_HOURS", "24"))
_password = os.getenv("ACUMEN_PASSWORD", "")

def verify_password(password: str) -> bool:
    if not _password:
        return False
    if len(password) != len(_password):
        return False
    result = 0
    for a, b in zip(password, _password):
        result |= ord(a) ^ ord(b)
    return result == 0

def create_token() -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"exp": expire, "sub": "acumen_user"}, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> bool:
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except Exception:
        return False