import secrets
import hashlib
import hmac
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from backend.app.core.config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${base64.b64encode(pwd_hash).decode()}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        salt, pwd_hash = stored.split("$")
        new_hash = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100000)
        return hmac.compare_digest(base64.b64encode(new_hash).decode(), pwd_hash)
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    return hmac.compare_digest(hash_api_key(api_key), hashed_key)


def sanitize_input(text: str) -> str:
    dangerous = ["<", ">", "&", "'", "\"", "/"]
    for ch in dangerous:
        text = text.replace(ch, "")
    return text.strip()[:10000]


def validate_command(command: str) -> bool:
    dangerous = ["rm -rf", "sudo", "chmod 777", "eval(", "exec(", "system(", "passthru(", "shell_exec(", "DROP TABLE", "DELETE FROM"]
    cmd_lower = command.lower()
    return not any(p in cmd_lower for p in dangerous)
