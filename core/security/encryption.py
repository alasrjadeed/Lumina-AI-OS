from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    HAS_CRYPTOGRAPHY = True
except ImportError:
    Fernet = None
    InvalidToken = None
    serialization = None
    rsa = None
    HAS_CRYPTOGRAPHY = False


@dataclass
class KeyPair:
    public_key: str
    private_key: str
    algorithm: str = "RSA"


class Encryption:
    """Symmetric and asymmetric encryption, hashing, key generation."""

    @staticmethod
    def hash_sha256(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def hash_md5(data: str) -> str:
        return hashlib.md5(data.encode()).hexdigest()

    @staticmethod
    def hash_file(path: str, algorithm: str = "sha256") -> str:
        h = hashlib.sha256() if algorithm == "sha256" else hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def hmac_sign(data: str, key: str, algorithm: str = "sha256") -> str:
        h = hashlib.sha256 if algorithm == "sha256" else hashlib.md5
        return hmac.new(key.encode(), data.encode(), h).hexdigest()

    @staticmethod
    def hmac_verify(data: str, key: str, signature: str) -> bool:
        expected = Encryption.hmac_sign(data, key)
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def generate_salt(length: int = 16) -> str:
        return secrets.token_hex(length)

    @staticmethod
    def generate_key(length: int = 32) -> str:
        return secrets.token_hex(length)

    @staticmethod
    def generate_key_pair(key_size: int = 2048) -> KeyPair:
        if not HAS_CRYPTOGRAPHY:
            return KeyPair(
                public_key="", private_key="", algorithm=f"RSA-{key_size} (cryptography required)"
            )
        assert rsa is not None and serialization is not None
        key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        private = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        public = (
            key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
        )
        return KeyPair(public_key=public, private_key=private)

    @staticmethod
    def encrypt_symmetric(data: str, key: str) -> str:
        if HAS_CRYPTOGRAPHY:
            assert Fernet is not None
            f = Fernet(base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()))
            return f.encrypt(data.encode()).decode()
        result = bytearray()
        for i, c in enumerate(data.encode()):
            result.append(c ^ ord(key[i % len(key)]))
        return base64.b64encode(bytes(result)).decode()

    @staticmethod
    def decrypt_symmetric(data: str, key: str) -> str:
        if HAS_CRYPTOGRAPHY:
            assert Fernet is not None and InvalidToken is not None
            f = Fernet(base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()))
            try:
                return f.decrypt(data.encode()).decode()
            except InvalidToken:
                return ""
        decoded = base64.b64decode(data.encode())
        result = bytearray()
        for i, c in enumerate(decoded):
            result.append(c ^ ord(key[i % len(key)]))
        return bytes(result).decode()

    @staticmethod
    def encrypt_file(path: str, key: str, output_path: str = "") -> str:
        out = output_path or path + ".enc"
        with open(path, "rb") as f:
            data = f.read()
        if HAS_CRYPTOGRAPHY:
            assert Fernet is not None
            f = Fernet(base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()))
            encrypted = f.encrypt(data)
        else:
            encrypted = bytearray()
            for i, b in enumerate(data):
                encrypted.append(b ^ ord(key[i % len(key)]))
            encrypted = bytes(encrypted)
        with open(out, "wb") as f:
            f.write(encrypted if isinstance(encrypted, bytes) else encrypted.encode())
        return out

    @staticmethod
    def decrypt_file(path: str, key: str, output_path: str = "") -> str:
        out = output_path or path.replace(".enc", ".dec")
        with open(path, "rb") as f:
            data = f.read()
        if HAS_CRYPTOGRAPHY:
            assert Fernet is not None
            f = Fernet(base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()))
            decrypted = f.decrypt(data)
        else:
            decrypted = bytearray()
            for i, b in enumerate(data):
                decrypted.append(b ^ ord(key[i % len(key)]))
            decrypted = bytes(decrypted)
        with open(out, "wb") as f:
            f.write(decrypted)
        return out
