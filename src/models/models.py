from tortoise.models import Model
from tortoise import fields

class Log(Model):
    id = fields.BigIntField(pk = True, description = "ID")

    user = fields.ForeignKeyField("e-starter.User", related_name="user", on_delete=fields.CASCADE)

    api = fields.TextField(description = "接口名称")
    action = fields.TextField(description = "行为描述")

    ip = fields.CharField(max_length=64, description = "操作IP")
    ua = fields.CharField(max_length=255, description = "访问UA")

    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "logs"

class User(Model):
    id = fields.BigIntField(pk = True, description = "ID")

    account = fields.CharField(max_length = 50, index = True, unique = True, description = "用户账号")
    password = fields.CharField(max_length = 64, description = "用户密码")

    open_id = fields.CharField(max_length = 32, index = True, description = "OPENID")

    logs = fields.ReverseRelation["Log"]
    
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "user"

class Role(Model):
    id = fields.IntField(pk=True, description="ID")
    role_name = fields.CharField(max_length=100, description="角色名")

    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "role"

class Permission(Model):
    id = fields.IntField(pk=True, description="ID")
    permission = fields.CharField(max_length=100, description="权限名")

    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "permission"

class UserRole(Model):
    id = fields.IntField(pk=True, description="ID")
    user = fields.ForeignKeyField("e-starter.User", related_name="roles", on_delete=fields.CASCADE)
    role = fields.ForeignKeyField("e-starter.Role", related_name="users", on_delete=fields.CASCADE)

    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "user_role"

class RolePermission(Model):
    id = fields.IntField(pk=True, description="ID")
    role = fields.ForeignKeyField("e-starter.Role", related_name="permissions", on_delete=fields.CASCADE)
    permission = fields.ForeignKeyField("e-starter.Permission", related_name="roles", on_delete=fields.CASCADE)

    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "role_permission"