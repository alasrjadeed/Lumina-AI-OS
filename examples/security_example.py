"""Lumina AI OS — Security Module Examples.

Demonstrates authentication, authorization, encryption,
secrets management, and audit logging.

Run: python examples/security_example.py
"""

import os
import tempfile

from core.security.audit import AuditLogger
from core.security.auth import Authentication
from core.security.authorization import Authorization, Permission
from core.security.encryption import Encryption
from core.security.secrets import SecretsManager


def demo_authentication():
    """User registration, login, session management."""
    print("\n1. Authentication")
    print("-" * 40)
    auth = Authentication()

    # Register
    user = auth.register_user("demo_user", "SecurePass123!")
    print(f"Registered: {user.username} (id: {user.id})")

    # Login
    session = auth.authenticate("demo_user", "SecurePass123!")
    assert session is not None
    print(f"Login token: {session.token[:16]}...")

    # Validate session
    assert session is not None
    validated = auth.validate_session(session.token)
    print(f"Session valid for: {validated.username if validated else 'INVALID'}")

    # API key
    api_key = auth.create_api_key("demo_user")
    print(f"API key: {api_key[:16]}...")

    # Logout
    assert session is not None
    auth.logout(session.token)
    print("Logged out.")


def demo_authorization():
    """Role-based access control."""
    print("\n2. Authorization (RBAC)")
    print("-" * 40)
    az = Authorization()

    # Check permissions
    print(f"Admin can do anything: {az.check_permission(['admin'], 'server', 'delete')}")
    print(f"User can read chat: {az.check_permission(['user'], 'chat', 'read')}")
    print(f"Viewer can create chat: {az.check_permission(['viewer'], 'chat', 'create')}")

    # Add custom permission
    az.add_permission("viewer", Permission(resource="profile", action="update"))
    print(f"Viewer can update profile: {az.check_permission(['viewer'], 'profile', 'update')}")


def demo_encryption():
    """Encryption, hashing, HMAC."""
    print("\n3. Encryption & Hashing")
    print("-" * 40)

    # Hashing
    h = Encryption.hash_sha256("hello")
    print(f"SHA256: {h[:16]}...")

    # HMAC
    sig = Encryption.hmac_sign("message", "secret-key")
    valid = Encryption.hmac_verify("message", "secret-key", sig)
    print(f"HMAC valid: {valid}")

    # Symmetric encryption
    key = Encryption.generate_key()
    encrypted = Encryption.encrypt_symmetric("sensitive data", key)
    decrypted = Encryption.decrypt_symmetric(encrypted, key)
    print(f"Encryption round-trip: {decrypted}")


def demo_secrets():
    """Secure secrets storage."""
    print("\n4. Secrets Management")
    print("-" * 40)
    with tempfile.TemporaryDirectory() as tmp:
        sm = SecretsManager(
            storage_path=os.path.join(tmp, "secrets.json"),
            master_key="master-key-123",
        )

        # Store secrets
        sm.set("db_password", "supersecret", tags=["database"])
        sm.set("api_key", "sk-abc123", tags=["api", "production"])
        print("Stored 2 secrets")

        # Retrieve
        print(f"DB password: {sm.get('db_password')}")
        print(f"API key: {sm.get('api_key')}")

        # List
        print(f"All keys: {sm.list_keys()}")

        # Search by tag
        found = sm.search_by_tag("database")
        print(f"Database secrets: {[s.key for s in found]}")


def demo_audit():
    """Tamper-evident audit logging."""
    print("\n5. Audit Logging")
    print("-" * 40)
    with tempfile.TemporaryDirectory() as tmp:
        al = AuditLogger(storage_path=os.path.join(tmp, "audit.json"))

        # Log events
        al.log("login", actor="alice", resource="system", result="success")
        al.log("file_read", actor="alice", resource="/etc/config.json", result="success")
        al.log(
            "login",
            actor="bob",
            resource="system",
            result="failure",
            details={"reason": "wrong password"},
        )

        # Query
        failures = al.get_failures()
        print(f"Failed events: {len(failures)}")
        for f in failures:
            print(f"  - {f.action} by {f.actor}: {f.details}")

        # Verify chain integrity
        tampered = al.verify_chain()
        print(f"Chain integrity: {'TAMPERED' if tampered else 'INTACT'}")


if __name__ == "__main__":
    print("=" * 60)
    print("Lumina Security Module Examples")
    print("=" * 60)

    demo_authentication()
    demo_authorization()
    demo_encryption()
    demo_secrets()
    demo_audit()

    print("\n" + "=" * 60)
    print("All security examples completed.")
    print("=" * 60)
