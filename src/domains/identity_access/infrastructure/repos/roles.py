from core.pagination import paginate_query

from ...domain import RoleListQuery, RoleReference
from ..models import Permission, Role


class RoleRepository:
    async def exists_by_name(self, role_name: str):
        return await Role.exists(role_name=role_name)

    async def get_by_name(self, role_name: str):
        return await Role.get_or_none(role_name=role_name)

    async def find(self, role: RoleReference):
        filters = role.as_filters()
        if not filters:
            return None
        return await Role.get_or_none(**filters)

    async def list(self, query: RoleListQuery):
        filters = query.as_filters()
        queryset = Role.filter(**filters) if filters else Role.all()
        return await paginate_query(queryset, query.page, query.page_size)

    async def create(self, role_name: str):
        return await Role.create(role_name=role_name)

    async def update(self, role_id: int, *, role_name: str | None = None):
        updates = {}
        if role_name is not None:
            updates["role_name"] = role_name
        query = Role.filter(id=role_id)
        if updates:
            await query.update(**updates)
        return await query.first()

    async def delete(self, role: RoleReference):
        return await Role.filter(**role.as_filters()).delete()

    async def has_permission(self, role: Role, permission: Permission):
        return permission in await role.permissions.all()

    async def add_permission(self, role: Role, permission: Permission):
        await role.permissions.add(permission)

    async def remove_permission(self, role: Role, permission: Permission):
        await role.permissions.remove(permission)
