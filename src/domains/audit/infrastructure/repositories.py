from core.pagination import paginate_query

from ..domain import AuditLogPage, AuditLogQuery, AuditLogRecord
from .models import AuditLog


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

    async def list_logs(self, query: AuditLogQuery):
        filters = query.to_filters()
        audit_query = AuditLog.filter(**filters) if filters else AuditLog.all()
        page_result = await paginate_query(audit_query, query.page, query.page_size)
        return AuditLogPage(
            items=page_result.items,
            total_items=page_result.total_items,
            total_pages=page_result.total_pages,
        )
