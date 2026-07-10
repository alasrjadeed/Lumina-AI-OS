from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field

try:
    from cryptography.fernet import Fernet

    HAS_FERNET = True
except ImportError:
    Fernet = None
    HAS_FERNET = False

from core.log import log


@dataclass
class Secret:
    key: str
    value: str
    encrypted: bool = False
    created: float = field(default_factory=time.time)
    rotated: float = 0.0
    version: int = 1
    tags: list[str] = field(default_factory=list)


class SecretsManager:
    """Secure storage for API keys, tokens, passwords with encryption at rest."""

    def __init__(self, storage_path: str = "lumina_secrets.json", master_key: str | None = None):
        self.storage_path = storage_path
        self._master_key = master_key or os.environ.get("LUMINA_MASTER_KEY", "")
        self._secrets: dict[str, Secret] = {}
        self._load()

    def set(
        self, key: str, value: str, tags: list[str] | None = None, encrypt: bool = True
    ) -> Secret:
        if key in self._secrets:
            existing = self._secrets[key]
            secret = Secret(
                key=key,
                value=value,
                encrypted=encrypt,
                created=existing.created,
                version=existing.version + 1,
                rotated=time.time(),
                tags=tags or existing.tags,
            )
        else:
            secret = Secret(key=key, value=value, encrypted=encrypt, tags=tags or [])
        if encrypt and self._master_key:
            secret.value = self._encrypt(value)
            secret.encrypted = True
        self._secrets[key] = secret
        self._save()
        log.info("Secret stored: %s (v%d, encrypted=%s)", key, secret.version, encrypt)
        return secret

    def get(self, key: str) -> str | None:
        secret = self._secrets.get(key)
        if not secret:
            return None
        if secret.encrypted and self._master_key:
            return self._decrypt(secret.value)
        return secret.value

    def get_metadata(self, key: str) -> Secret | None:
        return self._secrets.get(key)

    def delete(self, key: str) -> bool:
        if key in self._secrets:
            del self._secrets[key]
            self._save()
            return True
        return False

    def list_keys(self) -> list[str]:
        return list(self._secrets.keys())

    def list_secrets(self) -> list[Secret]:
        return list(self._secrets.values())

    def rotate(self, key: str, new_value: str) -> bool:
        if key not in self._secrets:
            return False
        self.set(key, new_value, encrypt=self._secrets[key].encrypted)
        return True

    def rotate_all(self, generator: Callable[..., str]) -> int:
        count = 0
        for key in list(self._secrets.keys()):
            try:
                new_value = generator(key)
                self.rotate(key, new_value)
                count += 1
            except Exception:
                pass
        return count

    def search_by_tag(self, tag: str) -> list[Secret]:
        return [s for s in self._secrets.values() if tag in s.tags]

    def exists(self, key: str) -> bool:
        return key in self._secrets

    def export(self, path: str = "") -> str:
        export_path = path or self.storage_path + ".export"
        data = {
            k: {
                "key": s.key,
                "value": s.value if not s.encrypted else "",
                "version": s.version,
                "encrypted": s.encrypted,
            }
            for k, s in self._secrets.items()
        }
        with open(export_path, "w") as f:
            json.dump(data, f, indent=2)
        return export_path

    def generate_key(self, length: int = 32) -> str:
        return secrets.token_hex(length)

    def generate_password(self, length: int = 24) -> str:
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return "".join(secrets.choice(chars) for _ in range(length))

    def _encrypt(self, value: str) -> str:
        if HAS_FERNET:
            key = base64.urlsafe_b64encode(hashlib.sha256(self._master_key.encode()).digest())
            assert Fernet is not None
            f = Fernet(key)
            return f.encrypt(value.encode()).decode()
        log.warning("cryptography not installed, using base64 encoding")
        return base64.b64encode(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        if HAS_FERNET:
            key = base64.urlsafe_b64encode(hashlib.sha256(self._master_key.encode()).digest())
            assert Fernet is not None
            f = Fernet(key)
            return f.decrypt(value.encode()).decode()
        log.warning("cryptography not installed, using base64 decoding")
        return base64.b64decode(value.encode()).decode()

    def _save(self) -> None:
        data = {
            k: {
                "key": s.key,
                "value": s.value,
                "encrypted": s.encrypted,
                "created": s.created,
                "rotated": s.rotated,
                "version": s.version,
                "tags": s.tags,
            }
            for k, s in self._secrets.items()
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                for k, v in data.items():
                    self._secrets[k] = Secret(**v)
            except Exception:
                pass
