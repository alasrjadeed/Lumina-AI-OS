from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Permission:
    resource: str
    action: str
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class Role:
    name: str
    permissions: list[Permission] = field(default_factory=list)
    inherits: list[str] = field(default_factory=list)


@dataclass
class Policy:
    name: str
    effect: str = "allow"
    resources: list[str] = field(default_factory=lambda: ["*"])
    actions: list[str] = field(default_factory=lambda: ["*"])
    subjects: list[str] = field(default_factory=lambda: ["*"])


class Authorization:
    """Role-based access control with policies, permissions, and role inheritance."""

    def __init__(self):
        self._roles: dict[str, Role] = {}
        self._policies: dict[str, Policy] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.add_role(Role(name="admin", permissions=[
            Permission(resource="*", action="*"),
        ]))
        self.add_role(Role(name="user", permissions=[
            Permission(resource="chat", action="create"),
            Permission(resource="chat", action="read"),
            Permission(resource="profile", action="*"),
        ]))
        self.add_role(Role(name="viewer", permissions=[
            Permission(resource="chat", action="read"),
            Permission(resource="profile", action="read"),
        ]))

    def add_role(self, role: Role) -> None:
        self._roles[role.name] = role

    def get_role(self, name: str) -> Role | None:
        return self._roles.get(name)

    def list_roles(self) -> list[Role]:
        return list(self._roles.values())

    def add_permission(self, role_name: str, permission: Permission) -> bool:
        role = self._roles.get(role_name)
        if not role:
            return False
        role.permissions.append(permission)
        return True

    def check_permission(self, user_roles: list[str], resource: str, action: str,
                         context: dict[str, Any] | None = None) -> bool:
        resolved = self._resolve_permissions(user_roles)
        return any(self._matches(perm, resource, action, context or {}) for perm in resolved)

    def check_policy(self, user_roles: list[str], resource: str, action: str) -> bool:
        for policy in self._policies.values():
            if self._policy_matches(policy, user_roles, resource, action):
                if policy.effect == "allow":
                    return True
                if policy.effect == "deny":
                    return False
        return False

    def add_policy(self, policy: Policy) -> None:
        self._policies[policy.name] = policy

    def get_effective_permissions(self, user_roles: list[str]) -> list[Permission]:
        return self._resolve_permissions(user_roles)

    def has_role(self, user_roles: list[str], role_name: str) -> bool:
        return role_name in user_roles

    def _resolve_permissions(self, user_roles: list[str]) -> list[Permission]:
        resolved: list[Permission] = []
        visited: set[str] = set()

        def resolve(role_name: str) -> None:
            if role_name in visited:
                return
            visited.add(role_name)
            role = self._roles.get(role_name)
            if not role:
                return
            resolved.extend(role.permissions)
            for inherited in role.inherits:
                resolve(inherited)

        for r in user_roles:
            resolve(r)
        return resolved

    def _matches(self, perm: Permission, resource: str, action: str,
                 context: dict[str, Any]) -> bool:
        if perm.resource != "*" and perm.resource != resource:
            return False
        if perm.action != "*" and perm.action != action:
            return False
        return all(context.get(key) == value for key, value in perm.conditions.items())

    def _policy_matches(self, policy: Policy, user_roles: list[str],
                        resource: str, action: str) -> bool:
        if "*" not in policy.subjects and not any(r in policy.subjects for r in user_roles):
            return False
        if "*" not in policy.resources and not any(
            self._glob_match(r, resource) for r in policy.resources
        ):
            return False
        return not ("*" not in policy.actions and action not in policy.actions)

    def _glob_match(self, pattern: str, value: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return value.startswith(pattern[:-1])
        return pattern == value
