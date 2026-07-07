from __future__ import annotations

import base64
import hmac
import json
import os
import time
from typing import Any

from fastapi import Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.settings import settings

try:
    from api.auth import auth_engine as _ae
except ImportError:
    _ae = None

security = HTTPBearer(auto_error=False)

AUTH_HEADER = "X-API-Key"
TOKEN_PREFIX = "Bearer "


def _verify_master_key(token: str) -> bool:
    master = os.environ.get("LUMINA_MASTER_KEY", "")
    if not master:
        return False
    return hmac.compare_digest(token, master)


def _verify_api_key(token: str) -> bool:
    if not settings.api_keys:
        return False
    keys = [k.strip() for k in settings.api_keys.split(",") if k.strip()]
    return token in keys


def _verify_jwt(token: str) -> dict[str, Any] | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


async def verify_request(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict[str, Any] | None:
    if not settings.auth_enabled:
        return None
    token = ""
    if credentials:
        token = credentials.credentials
    elif x_api_key:
        token = x_api_key
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    if _verify_master_key(token):
        return {"role": "admin", "method": "master_key"}
    if _verify_api_key(token):
        return {"role": "user", "method": "api_key"}
    payload = _verify_jwt(token)
    if payload:
        return {"role": payload.get("role", "user"), "method": "jwt", "sub": payload.get("sub")}
    # Check auth engine sessions
    if _ae is not None:
        user = _ae.validate_session(token)
        if user:
            return {"role": "user", "method": "session", "sub": user.id, "username": user.username}
    raise HTTPException(status_code=401, detail="Invalid authentication credentials")


async def require_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict[str, Any]:
    auth = await verify_request(request, credentials, x_api_key)
    if auth and auth.get("role") == "admin":
        return auth
    raise HTTPException(status_code=403, detail="Admin access required")
