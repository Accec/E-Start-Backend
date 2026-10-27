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
class AuditLogPage:
    items: list[object]
    total_items: int
    total_pages: int
