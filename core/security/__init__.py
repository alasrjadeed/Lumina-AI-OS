"""Security framework — authentication, authorization, encryption.

PBKDF2 password hashing, JWT/API key/master key auth, RBAC with
role inheritance and policies, Fernet symmetric encryption,
secrets vault with rotation, and tamper-evident audit chain.
"""

from core.security.audit import AuditEvent, AuditLogger
from core.security.auth import AuthConfig, Authentication, Session, User
from core.security.authorization import Authorization, Permission, Policy, Role
from core.security.encryption import Encryption, KeyPair
from core.security.secrets import Secret, SecretsManager

__all__ = [
    "Authentication",
    "AuthConfig",
    "User",
    "Session",
    "Authorization",
    "Role",
    "Permission",
    "Policy",
    "SecretsManager",
    "Secret",
    "Encryption",
    "KeyPair",
    "AuditLogger",
    "AuditEvent",
]
