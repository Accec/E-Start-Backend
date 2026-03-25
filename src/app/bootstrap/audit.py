from dataclasses import dataclass

from domains.audit.application import AuditLogService
from domains.audit.infrastructure.repositories import AuditLogRepository


@dataclass(slots=True)
class AuditBootstrap:
    audit_log_repository: AuditLogRepository
    audit_log_service: AuditLogService


__all__ = ["AuditBootstrap"]
