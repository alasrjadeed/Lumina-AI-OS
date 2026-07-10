import pytest

from kernel.plugins.version import (
    SemVer,
    check_plugin_compatibility,
    version_matches,
)


class TestSemVer:
    def test_parse_full(self):
        v = SemVer.parse("1.2.3-alpha.1+build.42")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.prerelease == "alpha.1"
        assert v.build == "build.42"

    def test_parse_minimal(self):
        v = SemVer.parse("0.0.1")
        assert v.major == 0
        assert v.minor == 0
        assert v.patch == 1

    def test_str(self):
        assert str(SemVer.parse("1.0.0")) == "1.0.0"
        assert str(SemVer.parse("2.3.4-rc1")) == "2.3.4-rc1"

    def test_ordering(self):
        assert SemVer(1, 0, 0) < SemVer(2, 0, 0)
        assert SemVer(1, 0, 0) == SemVer(1, 0, 0)
        assert SemVer(1, 1, 0) > SemVer(1, 0, 0)
        assert SemVer(1, 0, 2) > SemVer(1, 0, 1)

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid semver"):
            SemVer.parse("not.a.version")
        with pytest.raises(ValueError):
            SemVer.parse("1.2")
        with pytest.raises(ValueError):
            SemVer.parse("abc")


class TestVersionMatching:
    def test_exact_match(self):
        assert version_matches("1.0.0", SemVer(1, 0, 0))
        assert not version_matches("1.0.0", SemVer(1, 0, 1))

    def test_gt_lt(self):
        assert version_matches(">1.0.0", SemVer(2, 0, 0))
        assert not version_matches(">1.0.0", SemVer(0, 9, 0))
        assert version_matches("<2.0.0", SemVer(1, 0, 0))
        assert not version_matches("<2.0.0", SemVer(3, 0, 0))

    def test_gte_lte(self):
        assert version_matches(">=1.0.0", SemVer(1, 0, 0))
        assert version_matches(">=1.0.0", SemVer(2, 0, 0))
        assert not version_matches(">=2.0.0", SemVer(1, 0, 0))
        assert version_matches("<=2.0.0", SemVer(2, 0, 0))
        assert not version_matches("<=2.0.0", SemVer(3, 0, 0))

    def test_caret(self):
        assert version_matches("^1.0.0", SemVer(1, 5, 0))
        assert not version_matches("^1.0.0", SemVer(2, 0, 0))
        assert version_matches("^0.1.0", SemVer(0, 1, 5))
        assert not version_matches("^0.1.0", SemVer(0, 2, 0))

    def test_tilde(self):
        assert version_matches("~1.0.0", SemVer(1, 0, 5))
        assert not version_matches("~1.0.0", SemVer(1, 1, 0))


class TestCompatibility:
    def test_all_pass(self):
        errors = check_plugin_compatibility(
            "my_plugin",
            "1.0.0",
            {"dep_a": ">=1.0.0", "dep_b": "^2.0.0"},
            {"dep_a": "1.5.0", "dep_b": "2.3.0"},
        )
        assert errors == []

    def test_version_mismatch(self):
        errors = check_plugin_compatibility(
            "my_plugin",
            "1.0.0",
            {"dep_a": ">=2.0.0"},
            {"dep_a": "1.0.0"},
        )
        assert len(errors) == 1
        assert "does not satisfy" in errors[0]

    def test_missing_dependency(self):
        errors = check_plugin_compatibility(
            "my_plugin",
            "1.0.0",
            {"dep_missing": ">=1.0.0"},
            {"dep_a": "1.0.0"},
        )
        assert len(errors) == 1
        assert "not found" in errors[0]
