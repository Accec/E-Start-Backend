from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuditLogRecord:
    user_id: int
    api: str
    action: str
    ip: str
    ua: str
    level: int


@dataclass(frozen=True, slots=True)
class AuditLogQuery:
    page: int = 1
    page_size: int = 20
    id: int | None = None
    user_id: int | None = None
    api: str | None = None
    action: str | None = None
    ip: str | None = None
    ua: str | None = None
    level: int | None = None
    update_time: str | None = None
    create_time: str | None = None

    def to_filters(self) -> dict[str, object]:
        return {
            key: value
            for key, value in {
                "id": self.id,
                "user_id": self.user_id,
                "api": self.api,
                "action": self.action,
                "ip": self.ip,
                "ua": self.ua,
                "level": self.level,
                "update_time": self.update_time,
                "create_time": self.create_time,
            }.items()
            if value is not None
        }


@dataclass(frozen=True, slots=True)
class AuditLogPage:
    items: list[object]
    total_items: int
    total_pages: int
