from __future__ import annotations

from pathlib import Path

from core.vault.store import DataVault, VaultEntry, VaultProfile


class TestDataVault:
    def test_init_creates_empty_vault(self, tmp_path: Path):
        path = str(tmp_path / "vault.json")
        v = DataVault(path)
        assert v.count() == 0
        assert v.all() == {}

    def test_set_and_get(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        v.set("name", "Alice")
        assert v.get("name") == "Alice"

    def test_get_default(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        assert v.get("missing", "fallback") == "fallback"

    def test_set_many(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        v.set_many({"a": "1", "b": "2"})
        assert v.get("a") == "1"
        assert v.get("b") == "2"

    def test_delete_existent_key(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        v.set("x", "y")
        assert v.delete("x") is True
        assert v.get("x") == ""

    def test_delete_missing_key(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        assert v.delete("nonexistent") is False

    def test_all_returns_copy(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        v.set("k", "v")
        data = v.all()
        data["new"] = "added"
        assert "new" not in v.all()

    def test_clear(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        v.set_many({"a": "1", "b": "2"})
        v.clear()
        assert v.count() == 0

    def test_persistence(self, tmp_path: Path):
        path = str(tmp_path / "persist.json")
        v = DataVault(path)
        v.set("key", "value")
        v2 = DataVault(path)
        assert v2.get("key") == "value"

    def test_get_profile(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        v.set_many({"name": "Alice", "email": "alice@test.com", "phone": "123"})
        profile = v.get_profile()
        assert profile.name == "Alice"
        assert profile.email == "alice@test.com"
        assert profile.phone == "123"

    def test_set_profile(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        p = VaultProfile(name="Bob", email="bob@test.com", website="https://bob.com")
        v.set_profile(p)
        assert v.get("name") == "Bob"
        assert v.get("website") == "https://bob.com"

    def test_to_context_prompt(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        assert v.to_context_prompt() == ""
        v.set("name", "Alice")
        prompt = v.to_context_prompt()
        assert "Alice" in prompt
        assert "Name" in prompt

    def test_fill_template(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        v.set("name", "Alice")
        result = v.fill_template("Hello {{name}}!")
        assert result == "Hello Alice!"

    def test_fill_template_unknown_key(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        result = v.fill_template("{{missing}}")
        assert result == "{{missing}}"

    def test_missing_required(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        missing = v.missing_required()
        assert "name" in missing
        assert "email" in missing

    def test_missing_required_filled(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        v.set_many({"name": "A", "email": "b@c.com", "phone": "555"})
        assert v.missing_required() == []

    def test_count(self, tmp_path: Path):
        v = DataVault(str(tmp_path / "vault.json"))
        assert v.count() == 0
        v.set("a", "1")
        assert v.count() == 1


class TestVaultEntry:
    def test_defaults(self):
        e = VaultEntry(key="test", value="val")
        assert e.key == "test"
        assert e.value == "val"
        assert e.category == "personal"
        assert e.tags == []

    def test_with_all_fields(self):
        e = VaultEntry(key="k", value="v", category="business", label="Label", tags=["a", "b"])
        assert e.category == "business"
        assert e.label == "Label"
        assert e.tags == ["a", "b"]


class TestVaultProfile:
    def test_defaults(self):
        p = VaultProfile()
        assert p.name == ""
        assert p.tags == []

    def test_with_values(self):
        p = VaultProfile(name="Alice", email="a@b.com", tags=["vip"])
        assert p.name == "Alice"
        assert "vip" in p.tags
