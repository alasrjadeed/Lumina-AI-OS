from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field

from core.log import log


@dataclass
class User:
    id: str
    username: str
    password_hash: str = ""
    roles: list[str] = field(default_factory=list)
    api_keys: list[str] = field(default_factory=list)
    enabled: bool = True
    created: float = field(default_factory=time.time)


@dataclass
class Session:
    token: str
    user_id: str
    created: float = field(default_factory=time.time)
    expires: float = 0.0
    ip: str = ""


@dataclass
class AuthConfig:
    token_expiry: float = 86400
    session_expiry: float = 3600
    min_password_length: int = 8
    max_login_attempts: int = 5
    lockout_duration: float = 900


class Authentication:
    """User authentication with password hashing, tokens, sessions, and API keys."""

    def __init__(self, config: AuthConfig | None = None):
        self.config = config or AuthConfig()
        self._users: dict[str, User] = {}
        self._sessions: dict[str, Session] = {}
        self._login_attempts: dict[str, list[float]] = {}
        self._storage_path = "lumina_auth.json"

    def register_user(self, username: str, password: str, roles: list[str] | None = None) -> User:
        if len(password) < self.config.min_password_length:
            raise ValueError(
                f"Password must be at least {self.config.min_password_length} characters",
            )
        if username in self._users:
            raise ValueError(f"User already exists: {username}")
        user = User(
            id=self._generate_id(),
            username=username,
            password_hash=self._hash_password(password),
            roles=roles or ["user"],
        )
        self._users[username] = user
        self._save()
        log.info("User registered: %s", username)
        return user

    def authenticate(self, username: str, password: str) -> Session | None:
        if self._is_locked(username):
            log.warning("Account locked due to too many attempts: %s", username)
            return None
        user = self._users.get(username)
        if not user or not self._verify_password(password, user.password_hash):
            self._record_attempt(username)
            return None
        if not user.enabled:
            log.warning("Account disabled: %s", username)
            return None
        self._login_attempts.pop(username, None)
        session = Session(
            token=self._generate_token(),
            user_id=user.id,
            expires=time.time() + self.config.session_expiry,
        )
        self._sessions[session.token] = session
        self._save()
        log.info("User authenticated: %s", username)
        return session

    def validate_session(self, token: str) -> User | None:
        session = self._sessions.get(token)
        if not session:
            return None
        if time.time() > session.expires:
            self._sessions.pop(token, None)
            return None
        for user in self._users.values():
            if user.id == session.user_id:
                return user
        return None

    def logout(self, token: str) -> bool:
        return self._sessions.pop(token, None) is not None

    def create_api_key(self, username: str) -> str:
        user = self._users.get(username)
        if not user:
            raise ValueError(f"User not found: {username}")
        key = f"l sk-{secrets.token_hex(32)}"
        user.api_keys.append(key)
        self._save()
        return key

    def validate_api_key(self, key: str) -> User | None:
        for user in self._users.values():
            if key in user.api_keys and user.enabled:
                return user
        return None

    def revoke_api_key(self, username: str, key: str) -> bool:
        user = self._users.get(username)
        if not user or key not in user.api_keys:
            return False
        user.api_keys.remove(key)
        self._save()
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        user = self._users.get(username)
        if not user or not self._verify_password(old_password, user.password_hash):
            return False
        if len(new_password) < self.config.min_password_length:
            return False
        user.password_hash = self._hash_password(new_password)
        self._save()
        return True

    def disable_user(self, username: str) -> bool:
        user = self._users.get(username)
        if not user:
            return False
        user.enabled = False
        self._save()
        return True

    def enable_user(self, username: str) -> bool:
        user = self._users.get(username)
        if not user:
            return False
        user.enabled = True
        self._save()
        return True

    def get_user(self, username: str) -> User | None:
        return self._users.get(username)

    def list_users(self) -> list[User]:
        return list(self._users.values())

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return f"{salt}:{pwd_hash.hex()}"

    def _verify_password(self, password: str, stored: str) -> bool:
        salt, pwd_hash = stored.split(":")
        computed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(computed.hex(), pwd_hash)

    def _generate_token(self) -> str:
        return f"l_ses_{secrets.token_urlsafe(32)}"

    def _generate_id(self) -> str:
        return f"u_{secrets.token_hex(8)}"

    def _record_attempt(self, username: str) -> None:
        now = time.time()
        attempts = self._login_attempts.setdefault(username, [])
        attempts.append(now)
        cutoff = now - self.config.lockout_duration
        self._login_attempts[username] = [a for a in attempts if a > cutoff]

    def _is_locked(self, username: str) -> bool:
        attempts = self._login_attempts.get(username, [])
        return len(attempts) >= self.config.max_login_attempts

    def _save(self) -> None:
        data = {
            "users": {
                u.username: {
                    "id": u.id,
                    "username": u.username,
                    "password_hash": u.password_hash,
                    "roles": u.roles,
                    "api_keys": u.api_keys,
                    "enabled": u.enabled,
                    "created": u.created,
                }
                for u in self._users.values()
            },
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        if os.path.exists(self._storage_path):
            with open(self._storage_path) as f:
                data = json.load(f)
            for uname, udata in data.get("users", {}).items():
                self._users[uname] = User(**udata)
