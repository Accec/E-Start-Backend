from dataclasses import dataclass

from ..domain import EndpointReference, PermissionReference, RoleReference, UserReference

@dataclass(frozen=True, slots=True)
class CreateUserCommand:
    account: str | None
    password: str | None


@dataclass(frozen=True, slots=True)
class UpdateUserCommand:
    user_id: int | None
    account: str | None = None
    password: str | None = None

    def as_changes(self) -> dict[str, object]:
        changes: dict[str, object] = {}
        if self.account is not None:
            changes["account"] = self.account
        if self.password is not None:
            changes["password"] = self.password
        return changes


@dataclass(frozen=True, slots=True)
class CreateRoleCommand:
    role_name: str | None


@dataclass(frozen=True, slots=True)
class UpdateRoleCommand:
    role_id: int | None
    role_name: str | None

    def as_changes(self) -> dict[str, object]:
        changes: dict[str, object] = {}
        if self.role_name is not None:
            changes["role_name"] = self.role_name
        return changes


@dataclass(frozen=True, slots=True)
class CreatePermissionCommand:
    permission_title: str | None


@dataclass(frozen=True, slots=True)
class UpdatePermissionCommand:
    permission_id: int | None
    permission_title: str | None

    def as_changes(self) -> dict[str, object]:
        changes: dict[str, object] = {}
        if self.permission_title is not None:
            changes["permission_title"] = self.permission_title
        return changes


@dataclass(frozen=True, slots=True)
class UserRoleBinding:
    user: UserReference
    role: RoleReference


@dataclass(frozen=True, slots=True)
class RolePermissionBinding:
    role: RoleReference
    permission: PermissionReference


@dataclass(frozen=True, slots=True)
class EndpointPermissionBinding:
    endpoint: EndpointReference
    permission: PermissionReference


__all__ = [
    "CreatePermissionCommand",
    "CreateRoleCommand",
    "CreateUserCommand",
    "EndpointPermissionBinding",
    "RolePermissionBinding",
    "UpdatePermissionCommand",
    "UpdateRoleCommand",
    "UpdateUserCommand",
    "UserRoleBinding",
]
