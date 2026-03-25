from core.constants import LogLevel
from domains.audit.domain import AuditLogRecord
from domains.identity_access.application.ports import AuditLogWriter
from domains.identity_access.domain import RequestMeta


async def record_action(
    audit_logger: AuditLogWriter,
    actor_user_id: int,
    request_meta: RequestMeta,
    action: str,
    level: int = LogLevel.MEDIUM,
):
    await audit_logger.record(
        AuditLogRecord(
            user_id=actor_user_id,
            api=request_meta.api,
            action=action,
            ip=request_meta.ip,
            ua=request_meta.ua,
            level=level,
        )
    )
