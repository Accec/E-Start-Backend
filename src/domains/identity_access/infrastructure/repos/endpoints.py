from core.pagination import paginate_query

from ...domain import EndpointListQuery, EndpointReference
from ..models import Endpoint, Permission


class EndpointRepository:
    async def list_keys(self):
        records = await Endpoint.all().values_list("endpoint", "method")
        return {(endpoint, method) for endpoint, method in records}

    async def find(self, endpoint: EndpointReference):
        filters = endpoint.as_filters()
        if not filters:
            return None
        return await Endpoint.get_or_none(**filters)

    async def list(self, query: EndpointListQuery):
        filters = query.as_filters()
        queryset = Endpoint.filter(**filters) if filters else Endpoint.all()
        return await paginate_query(queryset, query.page, query.page_size)

    async def create(self, endpoint: str, method: str):
        return await Endpoint.create(endpoint=endpoint, method=method)

    async def delete_by_keys(self, endpoint_keys: set[tuple[str, str]]):
        if not endpoint_keys:
            return 0

        deleted = 0
        for endpoint, method in endpoint_keys:
            deleted += await Endpoint.filter(endpoint=endpoint, method=method).delete()
        return deleted

    async def has_permission(self, endpoint: Endpoint, permission: Permission):
        return permission in await endpoint.permissions.all()

    async def add_permission(self, endpoint: Endpoint, permission: Permission):
        await endpoint.permissions.add(permission)

    async def remove_permission(self, endpoint: Endpoint, permission: Permission):
        await endpoint.permissions.remove(permission)

    async def get_permission_titles(self, method: str, endpoint: str):
        endpoint_model = await Endpoint.get_or_none(endpoint=endpoint, method=method)
        if not endpoint_model:
            return set()
        permissions = await endpoint_model.permissions.all()
        return {permission.permission_title for permission in permissions}
