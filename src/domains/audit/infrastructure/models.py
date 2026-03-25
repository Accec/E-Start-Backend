from tortoise import fields
from tortoise.models import Model

from core.config import load_config
from core.constants import LogLevel


orm_app_label = load_config().app


class AuditLog(Model):
    # Audit queries are usually filtered by API, action, and actor metadata, so
    # those columns stay indexed to keep the admin trail usable at scale.
    id = fields.BigIntField(primary_key=True, description="ID")
    user = fields.ForeignKeyField(f"{orm_app_label}.User", related_name="logs", on_delete=fields.CASCADE)
    api = fields.CharField(max_length=512, db_index=True, description="API URI")
    action = fields.CharField(max_length=512, db_index=True, description="Action summary")
    ip = fields.CharField(db_index=True, max_length=64, description="Source IP")
    ua = fields.CharField(db_index=True, max_length=255, description="User agent")
    level = fields.IntEnumField(LogLevel, db_index=True, description="Severity level")
    update_time = fields.DatetimeField(auto_now=True, description="Updated at")
    create_time = fields.DatetimeField(auto_now_add=True, description="Created at")

    class Meta:
        table = "log"
