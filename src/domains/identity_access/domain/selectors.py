from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserReference:
    user_id: int | None = None
    account: str | None = None

    def as_filters(self) -> dict[str, object]:
        filters: dict[str, object] = {}
        if self.user_id is not None:
            filters["id"] = self.user_id
        if self.account is not None:
            filters["account"] = self.account
        return filters


@dataclass(frozen=True, slots=True)
class RoleReference:
    role_id: int | None = None
    role_name: str | None = None

    def as_filters(self) -> dict[str, object]:
        filters: dict[str, object] = {}
        if self.role_id is not None:
            filters["id"] = self.role_id
        if self.role_name is not None:
            filters["role_name"] = self.role_name
        return filters


@dataclass(frozen=True, slots=True)
class PermissionReference:
    permission_id: int | None = None
    permission_title: str | None = None

    def as_filters(self) -> dict[str, object]:
        filters: dict[str, object] = {}
        if self.permission_id is not None:
            filters["id"] = self.permission_id
        if self.permission_title is not None:
            filters["permission_title"] = self.permission_title
        return filters


@dataclass(frozen=True, slots=True)
class EndpointReference:
    endpoint_id: int | None = None
    endpoint_path: str | None = None
    method: str | None = None

    def as_filters(self) -> dict[str, object]:
        filters: dict[str, object] = {}
        if self.endpoint_id is not None:
            filters["id"] = self.endpoint_id
        if self.endpoint_path is not None:
            filters["endpoint"] = self.endpoint_path
        if self.method is not None:
            filters["method"] = self.method
        return filters


@dataclass(frozen=True, slots=True)
class UserListQuery(UserReference):
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True, slots=True)
class RoleListQuery(RoleReference):
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True, slots=True)
class PermissionListQuery(PermissionReference):
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True, slots=True)
class EndpointListQuery(EndpointReference):
    page: int = 1
    page_size: int = 20


__all__ = [
    "EndpointListQuery",
    "EndpointReference",
    "PermissionListQuery",
    "PermissionReference",
    "RoleListQuery",
    "RoleReference",
    "UserListQuery",
    "UserReference",
]
