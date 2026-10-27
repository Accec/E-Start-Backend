from core.pagination import paginate_query

from ..records import AuditLogPage, AuditLogRecord
from ..models import AuditLog


class AuditLogRepository:
    async def record(self, record: AuditLogRecord):
        return await AuditLog.create(
            user_id=record.user_id,
            api=record.api,
            action=record.action,
            ip=record.ip,
            ua=record.ua,
            level=record.level,
        )

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
        filters = {
            key: value
            for key, value in {
                "id": id,
                "user_id": user_id,
                "api": api,
                "action": action,
                "ip": ip,
                "ua": ua,
                "level": level,
                "update_time": update_time,
                "create_time": create_time,
            }.items()
            if value is not None
        }
        audit_query = AuditLog.filter(**filters) if filters else AuditLog.all()
        page_result = await paginate_query(audit_query, page, page_size)
        return AuditLogPage(
            items=page_result.items,
            total_items=page_result.total_items,
            total_pages=page_result.total_pages,
        )
