from tortoise.models import Model
from tortoise import fields
from utils.constant import LogLevel, UserStatus



class Log(Model):
    id = fields.BigIntField(pk = True, description = "ID")

    user = fields.ForeignKeyField("e-starter.User", related_name="log", on_delete=fields.CASCADE)

    api = fields.CharField(max_length=512, index = True, description = "接口URI")
    action = fields.CharField(max_length=512, index = True, description = "行为描述")

    ip = fields.CharField(index = True, max_length=64, description = "操作IP")
    ua = fields.CharField(index = True, max_length=255, description = "访问UA")

    level = fields.IntEnumField(LogLevel, index = True, description = "日志等级")

    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "log"

class User(Model):
    id = fields.BigIntField(pk = True, description = "ID")

    account = fields.CharField(max_length = 50, index = True, unique = True, description = "用户账号")
    password = fields.CharField(max_length = 32, description = "用户密码")

    open_id = fields.CharField(max_length = 32, index = True, unique = True, description = "OPENID")

    status = fields.IntEnumField(UserStatus, index = True, description = "用户状态")

    logs = fields.ReverseRelation["Log"]
    roles = fields.ManyToManyField('e-starter.Role', related_name='users', through='user_role')
    
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "user"

class Role(Model):
    id = fields.IntField(pk=True, description="ID")
    role_name = fields.CharField(max_length=100, unique = True, description="角色名")

    permissions = fields.ManyToManyField('e-starter.Permission', related_name='roles', through='role_permission')

    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "role"

class Permission(Model):
    id = fields.IntField(pk=True, description="ID")
    permission_title = fields.CharField(index = True, unique = True, max_length=100, description="权限名")

    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "permission"

class Endpoint(Model):
    id = fields.IntField(pk=True, description="ID")
    endpoint = fields.CharField(index = True, max_length=255, description="终端名")
    method = fields.CharField(max_length=10, description="请求方式")

    permissions = fields.ManyToManyField('e-starter.Permission', related_name='endpoints', through='endpoint_permission')

    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "endpoint"
        unique_together = ("endpoint", "method")