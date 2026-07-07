from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.security.audit import AuditLogger
from core.security.auth import AuthConfig, Authentication
from core.security.authorization import Authorization, Permission, Policy, Role
from core.security.encryption import Encryption
from core.security.secrets import SecretsManager


class TestAuthentication:
    def test_register_user(self):
        auth = Authentication()
        user = auth.register_user("alice", "securepass123")
        assert user.username == "alice"
        assert "user" in user.roles

    def test_register_duplicate(self):
        auth = Authentication()
        auth.register_user("bob", "securepass123")
        with pytest.raises(ValueError):
            auth.register_user("bob", "otherpass")

    def test_register_short_password(self):
        auth = Authentication()
        with pytest.raises(ValueError):
            auth.register_user("c", "short")

    def test_authenticate_success(self):
        auth = Authentication()
        auth.register_user("dave", "mypassword")
        session = auth.authenticate("dave", "mypassword")
        assert session is not None
        assert session.token.startswith("l_ses_")

    def test_authenticate_wrong_password(self):
        auth = Authentication()
        auth.register_user("eve", "correctpass")
        session = auth.authenticate("eve", "wrongpass")
        assert session is None

    def test_authenticate_nonexistent(self):
        auth = Authentication()
        session = auth.authenticate("nonexistent", "pass")
        assert session is None

    def test_validate_session(self):
        auth = Authentication()
        auth.register_user("frank", "password")
        session = auth.authenticate("frank", "password")
        user = auth.validate_session(session.token)
        assert user is not None
        assert user.username == "frank"

    def test_validate_expired_session(self):
        auth = Authentication(config=AuthConfig(session_expiry=-1))
        auth.register_user("grace", "password")
        session = auth.authenticate("grace", "password")
        user = auth.validate_session(session.token)
        assert user is None

    def test_logout(self):
        auth = Authentication()
        auth.register_user("heidi", "password")
        session = auth.authenticate("heidi", "password")
        assert auth.logout(session.token)
        assert auth.validate_session(session.token) is None

    def test_api_key(self):
        auth = Authentication()
        auth.register_user("ivan", "password")
        key = auth.create_api_key("ivan")
        assert key.startswith("l sk-")
        user = auth.validate_api_key(key)
        assert user is not None
        assert auth.revoke_api_key("ivan", key)
        assert auth.validate_api_key(key) is None

    def test_change_password(self):
        auth = Authentication()
        auth.register_user("judy", "oldpass123")
        assert auth.change_password("judy", "oldpass123", "newpass456")
        session = auth.authenticate("judy", "newpass456")
        assert session is not None
        assert not auth.change_password("judy", "wrong", "newerpass789")

    def test_disable_enable_user(self):
        auth = Authentication()
        auth.register_user("karl", "password")
        assert auth.disable_user("karl")
        assert auth.authenticate("karl", "password") is None
        assert auth.enable_user("karl")
        assert auth.authenticate("karl", "password") is not None

    def test_list_users(self):
        auth = Authentication()
        auth.register_user("u1", "password")
        auth.register_user("u2", "password")
        assert len(auth.list_users()) >= 2

    def test_get_user(self):
        auth = Authentication()
        auth.register_user("lucy", "password")
        user = auth.get_user("lucy")
        assert user is not None
        assert auth.get_user("nonexistent") is None

    def test_lockout(self):
        config = AuthConfig(max_login_attempts=2, lockout_duration=60)
        auth = Authentication(config=config)
        auth.register_user("mal", "password")
        auth.authenticate("mal", "wrong")
        auth.authenticate("mal", "wrong")
        assert auth.authenticate("mal", "password") is None


class TestAuthorization:
    def test_default_roles_exist(self):
        az = Authorization()
        assert az.get_role("admin") is not None
        assert az.get_role("user") is not None
        assert az.get_role("viewer") is not None

    def test_add_role(self):
        az = Authorization()
        az.add_role(Role(name="custom"))
        assert az.get_role("custom") is not None

    def test_check_permission_admin(self):
        az = Authorization()
        assert az.check_permission(["admin"], "anything", "anything")

    def test_check_permission_user(self):
        az = Authorization()
        assert az.check_permission(["user"], "chat", "create")
        assert not az.check_permission(["user"], "admin_panel", "delete")

    def test_check_permission_viewer(self):
        az = Authorization()
        assert az.check_permission(["viewer"], "chat", "read")
        assert not az.check_permission(["viewer"], "chat", "create")

    def test_add_permission(self):
        az = Authorization()
        assert az.add_permission("viewer", Permission(resource="profile", action="update"))
        assert az.check_permission(["viewer"], "profile", "update")

    def test_add_permission_nonexistent_role(self):
        az = Authorization()
        assert not az.add_permission("missing", Permission(resource="x", action="y"))

    def test_has_role(self):
        az = Authorization()
        assert az.has_role(["admin", "user"], "admin")
        assert not az.has_role(["user"], "admin")

    def test_get_effective_permissions(self):
        az = Authorization()
        perms = az.get_effective_permissions(["admin"])
        assert len(perms) >= 1

    def test_policy_allow(self):
        az = Authorization()
        az.add_policy(Policy(name="allow_chat", effect="allow",
                             resources=["chat"], actions=["read"]))
        assert az.check_policy(["user"], "chat", "read")

    def test_policy_deny(self):
        az = Authorization()
        az.add_policy(Policy(name="deny_admin", effect="deny",
                             resources=["admin"], actions=["*"]))
        assert not az.check_policy(["admin"], "admin", "delete")

    def test_list_roles(self):
        az = Authorization()
        assert len(az.list_roles()) >= 3


class TestSecretsManager:
    def test_set_and_get(self, tmp_path: Path):
        sm = SecretsManager(
            storage_path=str(tmp_path / "secrets.json"), master_key="test-master-key",
        )
        sm.set("api_key", "sk-12345")
        assert sm.get("api_key") == "sk-12345"

    def test_get_nonexistent(self, tmp_path: Path):
        sm = SecretsManager(storage_path=str(tmp_path / "secrets.json"))
        assert sm.get("nonexistent") is None

    def test_delete(self, tmp_path: Path):
        sm = SecretsManager(storage_path=str(tmp_path / "secrets.json"))
        sm.set("temp", "value")
        assert sm.delete("temp")
        assert not sm.delete("nonexistent")

    def test_list_keys(self, tmp_path: Path):
        sm = SecretsManager(storage_path=str(tmp_path / "secrets.json"))
        sm.set("k1", "v1")
        sm.set("k2", "v2")
        keys = sm.list_keys()
        assert "k1" in keys
        assert "k2" in keys

    def test_rotate(self, tmp_path: Path):
        sm = SecretsManager(storage_path=str(tmp_path / "secrets.json"), master_key="mk")
        sm.set("key", "old_value")
        sm.rotate("key", "new_value")
        assert sm.get("key") == "new_value"
        assert sm.get_metadata("key").version == 2

    def test_search_by_tag(self, tmp_path: Path):
        sm = SecretsManager(storage_path=str(tmp_path / "secrets.json"))
        sm.set("db_pass", "secret", tags=["database", "production"])
        results = sm.search_by_tag("database")
        assert len(results) == 1

    def test_generate_key(self, tmp_path: Path):
        sm = SecretsManager(storage_path=str(tmp_path / "secrets.json"))
        key = sm.generate_key(16)
        assert len(key) == 32

    def test_generate_password(self, tmp_path: Path):
        sm = SecretsManager(storage_path=str(tmp_path / "secrets.json"))
        pwd = sm.generate_password(20)
        assert len(pwd) == 20

    def test_exists(self, tmp_path: Path):
        sm = SecretsManager(storage_path=str(tmp_path / "secrets.json"))
        sm.set("exists_key", "val")
        assert sm.exists("exists_key")
        assert not sm.exists("missing")


class TestEncryption:
    def test_hash_sha256(self):
        h = Encryption.hash_sha256("hello")
        assert len(h) == 64
        assert h == Encryption.hash_sha256("hello")
        assert h != Encryption.hash_sha256("world")

    def test_hash_md5(self):
        h = Encryption.hash_md5("hello")
        assert len(h) == 32

    def test_hmac_sign_and_verify(self):
        sig = Encryption.hmac_sign("data", "key")
        assert Encryption.hmac_verify("data", "key", sig)
        assert not Encryption.hmac_verify("data", "wrong_key", sig)

    def test_generate_salt(self):
        s1 = Encryption.generate_salt()
        s2 = Encryption.generate_salt()
        assert len(s1) == 32
        assert s1 != s2

    def test_generate_key(self):
        k = Encryption.generate_key(16)
        assert len(k) == 32

    def test_symmetric_encrypt_decrypt(self):
        key = Encryption.generate_key()
        data = "secret message"
        encrypted = Encryption.encrypt_symmetric(data, key)
        assert encrypted != data
        decrypted = Encryption.decrypt_symmetric(encrypted, key)
        assert decrypted == data

    def test_symmetric_wrong_key(self):
        data = "test"
        enc = Encryption.encrypt_symmetric(data, "key1")
        dec = Encryption.decrypt_symmetric(enc, "key2")
        assert dec != data

    def test_hash_file(self, tmp_path: Path):
        path = str(tmp_path / "test.txt")
        Path(path).write_text("hello")
        h = Encryption.hash_file(path)
        assert len(h) == 64

    def test_generate_key_pair(self):
        kp = Encryption.generate_key_pair(2048)
        assert kp.algorithm.startswith("RSA")


class TestAuditLogger:
    def test_log_event(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        event = al.log("login", actor="alice", resource="system", result="success")
        assert event.action == "login"
        assert event.actor == "alice"
        assert event.hash

    def test_query(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        al.log("login", actor="alice")
        al.log("logout", actor="alice")
        al.log("login", actor="bob")
        results = al.query(action="login")
        assert len(results) == 2
        results = al.query(actor="alice")
        assert len(results) == 2

    def test_get_recent(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        al.log("event1")
        al.log("event2")
        recent = al.get_recent(1)
        assert len(recent) == 1
        assert recent[0].action == "event2"

    def test_get_by_user(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        al.log("login", actor="alice")
        al.log("login", actor="bob")
        results = al.get_by_user("alice")
        assert len(results) == 1

    def test_get_failures(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        al.log("login", result="success")
        al.log("login", result="failure")
        failures = al.get_failures()
        assert len(failures) == 1

    def test_verify_chain(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        al.log("e1")
        al.log("e2")
        al.log("e3")
        tampered = al.verify_chain()
        assert tampered == []

    def test_verify_event(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        al.log("test")
        assert al.verify_event(0)
        assert not al.verify_event(99)

    def test_count(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        assert al.count() == 0
        al.log("test")
        assert al.count() == 1

    def test_export_json(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        al.log("test")
        path = al.export(str(tmp_path / "export.json"), format="json")
        assert Path(path).exists()

    def test_clear(self, tmp_path: Path):
        al = AuditLogger(storage_path=str(tmp_path / "audit.json"))
        al.log("test")
        al.clear()
        assert al.count() == 0

    def test_chain_tamper_detection(self, tmp_path: Path):
        path = str(tmp_path / "tamper.json")
        al = AuditLogger(storage_path=path)
        al.log("e1")
        al.log("e2")
        with open(path) as f:
            data = json.load(f)
        data[1]["action"] = "TAMPERED"
        with open(path, "w") as f:
            json.dump(data, f)
        al2 = AuditLogger(storage_path=path)
        tampered = al2.verify_chain()
        assert len(tampered) > 0
