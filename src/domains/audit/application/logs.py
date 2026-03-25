from .ports import AuditLogStore
from ..domain import AuditLogQuery, AuditLogRecord


class AuditLogService:
    def __init__(self, *, logs: AuditLogStore):
        self.logs = logs

    async def record(self, record: AuditLogRecord):
        return await self.logs.record(record)

    async def list_logs(self, query: AuditLogQuery):
        return await self.logs.list_logs(query)
