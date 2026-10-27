from dataclasses import dataclass

from core.constants import LogLevel
from domains.audit.records import AuditLogRecord

from .ports import AuditLogWriter


@dataclass(frozen=True, slots=True)
class RequestMeta:
    api: str
    ip: str
    ua: str


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
