from core.pagination import paginate_query

from ..models import Permission


class PermissionRepository:
    async def exists_by_title(self, permission_title: str):
        return await Permission.exists(permission_title=permission_title)

    async def find(self, *, permission_id: int | None = None, permission_title: str | None = None):
        filters = {
            key: value
            for key, value in {"id": permission_id, "permission_title": permission_title}.items()
            if value is not None
        }
        if not filters:
            return None
        return await Permission.get_or_none(**filters)

    async def list(
        self,
        *,
        permission_id: int | None = None,
        permission_title: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        filters = {
            key: value
            for key, value in {"id": permission_id, "permission_title": permission_title}.items()
            if value is not None
        }
        queryset = Permission.filter(**filters) if filters else Permission.all()
        return await paginate_query(queryset, page, page_size)

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

    async def delete(self, *, permission_id: int | None = None, permission_title: str | None = None) -> int:
        filters = {
            key: value
            for key, value in {"id": permission_id, "permission_title": permission_title}.items()
            if value is not None
        }
        if not filters:
            return 0
        return await Permission.filter(**filters).delete()
