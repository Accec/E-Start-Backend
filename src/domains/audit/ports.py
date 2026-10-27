from typing import Protocol

from .records import AuditLogPage, AuditLogRecord


class AuditLogStore(Protocol):
    async def record(self, record: AuditLogRecord): ...

    async def list_logs(
        self,
        *,
        id: int | None = None,
        user_id: int | None = None,
        api: str | None = None,
        action: str | None = None,
        ip: str | None = None,
        ua: str | None = None,
        level: int | None = None,
        update_time: str | None = None,
        create_time: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditLogPage: ...


__all__ = ["AuditLogStore"]
