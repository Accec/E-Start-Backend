from core.pagination import paginate_query

from ...domain import PermissionListQuery, PermissionReference
from ..models import Permission


class PermissionRepository:
    async def exists_by_title(self, permission_title: str):
        return await Permission.exists(permission_title=permission_title)

    async def find(self, permission: PermissionReference):
        filters = permission.as_filters()
        if not filters:
            return None
        return await Permission.get_or_none(**filters)

    async def list(self, query: PermissionListQuery):
        filters = query.as_filters()
        queryset = Permission.filter(**filters) if filters else Permission.all()
        return await paginate_query(queryset, query.page, query.page_size)

    async def create(self, permission_title: str):
        return await Permission.create(permission_title=permission_title)

    async def update(self, permission_id: int, *, permission_title: str | None = None):
        updates = {}
        if permission_title is not None:
            updates["permission_title"] = permission_title
        query = Permission.filter(id=permission_id)
        if updates:
            await query.update(**updates)
        return await query.first()

    async def delete(self, permission: PermissionReference):
        return await Permission.filter(**permission.as_filters()).delete()
