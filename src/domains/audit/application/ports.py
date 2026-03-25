from typing import Protocol

from ..domain import AuditLogPage, AuditLogQuery, AuditLogRecord


class AuditLogStore(Protocol):
    async def record(self, record: AuditLogRecord): ...

    async def list_logs(self, query: AuditLogQuery) -> AuditLogPage: ...


__all__ = ["AuditLogStore"]
