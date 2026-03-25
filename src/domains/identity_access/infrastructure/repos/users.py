import asyncio

from core.pagination import paginate_query

from ...domain import UserListQuery, UserReference
from ..models import Role, User


class UserRepository:
    async def get_by_account(self, account: str):
        return await User.get_or_none(account=account)

    async def get_by_id(self, user_id: int):
        return await User.get_or_none(id=user_id)

    async def find(self, user: UserReference):
        filters = user.as_filters()
        if not filters:
            return None
        return await User.get_or_none(**filters)

    async def exists_by_account(self, account: str):
        return await User.exists(account=account)

    async def list(self, query: UserListQuery):
        filters = query.as_filters()
        queryset = User.filter(**filters) if filters else User.all()
        return await paginate_query(queryset, query.page, query.page_size)

    async def create(self, account: str, password: str, open_id: str):
        return await User.create(account=account, password=password, open_id=open_id)

    async def update(self, user_id: int, *, account: str | None = None, password: str | None = None):
        updates = {}
        if account is not None:
            updates["account"] = account
        if password is not None:
            updates["password"] = password
        query = User.filter(id=user_id)
        if updates:
            await query.update(**updates)
        return await query.first()

    async def list_roles(self, user: User):
        return await user.roles.all()

    async def add_role(self, user: User, role: Role):
        await user.roles.add(role)

    async def remove_role(self, user: User, role: Role):
        await user.roles.remove(role)

    async def has_role(self, user: User, role: Role):
        return role in await user.roles.all()

    async def collect_dashboard(self, user_id: int):
        user = await User.get(id=user_id)
        roles = await user.roles.all()
        permission_groups = await asyncio.gather(*(role.permissions.all() for role in roles))
        permissions = {permission for group in permission_groups for permission in group}
        endpoint_groups = await asyncio.gather(*(permission.endpoints.all() for permission in permissions))
        endpoints = {endpoint for group in endpoint_groups for endpoint in group}
        return user, roles, list(permissions), list(endpoints)

    async def get_permission_titles(self, user_id: int):
        user = await User.get(id=user_id)
        roles = await user.roles.all()
        permission_groups = await asyncio.gather(*(role.permissions.all() for role in roles))
        return {permission.permission_title for group in permission_groups for permission in group}
