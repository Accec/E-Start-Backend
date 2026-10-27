from ..ports import AuditLogStore
from ..records import AuditLogPage, AuditLogRecord


class AuditLogService:
    def __init__(self, *, logs: AuditLogStore):
        self.logs = logs

    async def record(self, record: AuditLogRecord):
        return await self.logs.record(record)

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
    ) -> AuditLogPage:
        return await self.logs.list_logs(
            id=id,
            user_id=user_id,
            api=api,
            action=action,
            ip=ip,
            ua=ua,
            level=level,
            update_time=update_time,
            create_time=create_time,
            page=page,
            page_size=page_size,
        )
