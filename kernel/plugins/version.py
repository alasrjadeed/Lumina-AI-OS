from __future__ import annotations

import re
from dataclasses import dataclass

_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z.-]+))?"
    r"(?:\+(?P<build>[0-9A-Za-z.-]+))?$",
)

_RANGE_RE = re.compile(
    r"^\s*(?P<op>>=|<=|>|<|==|\^|~|=)?\s*"
    r"(?P<ver>"
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?: \+[0-9A-Za-z.-]+)?"
    r")\s*$",
)


@dataclass(frozen=True, order=True)
class SemVer:
    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: str = ""
    build: str = ""

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            s += f"-{self.prerelease}"
        if self.build:
            s += f"+{self.build}"
        return s

    @classmethod
    def parse(cls, version: str) -> SemVer:
        m = _SEMVER_RE.match(version.strip())
        if not m:
            raise ValueError(f"Invalid semver: {version}")
        return cls(
            major=int(m.group("major")),
            minor=int(m.group("minor")),
            patch=int(m.group("patch")),
            prerelease=m.group("prerelease") or "",
            build=m.group("build") or "",
        )


def _parse_range_spec(spec: str) -> tuple[str, SemVer]:
    m = _RANGE_RE.match(spec.strip())
    if not m:
        raise ValueError(f"Invalid version specifier: {spec}")
    return m.group("op") or "=", SemVer.parse(m.group("ver"))


def _check_caret(base: SemVer, version: SemVer) -> bool:
    if base.major != 0:
        return base <= version < SemVer(base.major + 1, 0, 0)
    if base.minor != 0:
        return base <= version < SemVer(0, base.minor + 1, 0)
    return base <= version < SemVer(0, 0, base.patch + 1)


def _check_tilde(base: SemVer, version: SemVer) -> bool:
    return base <= version < SemVer(base.major, base.minor + 1, 0)


def version_matches(spec: str, version: SemVer) -> bool:
    op, base = _parse_range_spec(spec)
    if op == "=":
        return version == base
    if op == ">=":
        return version >= base
    if op == "<=":
        return version <= base
    if op == ">":
        return version > base
    if op == "<":
        return version < base
    if op == "^":
        return _check_caret(base, version)
    if op == "~":
        return _check_tilde(base, version)
    if op == "==":
        return version == base
    return False


def check_plugin_compatibility(
    plugin_name: str,
    plugin_version: str,
    requirements: dict[str, str],
    available: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    for dep_name, spec in requirements.items():
        dep_ver = available.get(dep_name)
        if dep_ver is None:
            errors.append(f"{plugin_name}: dependency '{dep_name}' not found")
            continue
        try:
            dv = SemVer.parse(dep_ver)
        except ValueError as e:
            errors.append(f"{plugin_name}: invalid version '{dep_ver}' for '{dep_name}': {e}")
            continue
        if not version_matches(spec, dv):
            errors.append(
                f"{plugin_name}: dependency '{dep_name}' version {dep_ver} does not satisfy {spec}"
            )
    return errors
