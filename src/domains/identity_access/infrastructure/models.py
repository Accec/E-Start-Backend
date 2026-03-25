from tortoise import fields
from tortoise.models import Model

from core.config import load_config
from core.constants import UserStatus


orm_app_label = load_config().app


class User(Model):
    id = fields.BigIntField(primary_key=True, description="ID")
    account = fields.CharField(max_length=50, db_index=True, unique=True, description="User account")
    password = fields.CharField(max_length=255, description="Password hash")
    open_id = fields.CharField(max_length=32, db_index=True, unique=True, description="OpenID")
    status = fields.IntEnumField(UserStatus, default=UserStatus.ACTIVE, db_index=True, description="User status")

    logs = fields.ReverseRelation["AuditLog"]
    roles = fields.ManyToManyField(f"{orm_app_label}.Role", related_name="users", through="user_role")

    update_time = fields.DatetimeField(auto_now=True, description="Updated at")
    create_time = fields.DatetimeField(auto_now_add=True, description="Created at")

    class Meta:
        table = "user"


class Role(Model):
    id = fields.IntField(primary_key=True, description="ID")
    role_name = fields.CharField(max_length=100, unique=True, description="Role name")

    permissions = fields.ManyToManyField(f"{orm_app_label}.Permission", related_name="roles", through="role_permission")

    update_time = fields.DatetimeField(auto_now=True, description="Updated at")
    create_time = fields.DatetimeField(auto_now_add=True, description="Created at")

    class Meta:
        table = "role"


class Permission(Model):
    id = fields.IntField(primary_key=True, description="ID")
    permission_title = fields.CharField(db_index=True, unique=True, max_length=100, description="Permission title")

    update_time = fields.DatetimeField(auto_now=True, description="Updated at")
    create_time = fields.DatetimeField(auto_now_add=True, description="Created at")

    class Meta:
        table = "permission"


class Endpoint(Model):
    id = fields.IntField(primary_key=True, description="ID")
    endpoint = fields.CharField(db_index=True, max_length=255, description="Endpoint path")
    method = fields.CharField(max_length=10, description="HTTP method")

    permissions = fields.ManyToManyField(
        f"{orm_app_label}.Permission",
        related_name="endpoints",
        through="endpoint_permission",
    )

    update_time = fields.DatetimeField(auto_now=True, description="Updated at")
    create_time = fields.DatetimeField(auto_now_add=True, description="Created at")

    class Meta:
        table = "endpoint"
        unique_together = ("endpoint", "method")
