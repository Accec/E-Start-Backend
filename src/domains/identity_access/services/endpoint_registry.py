from dataclasses import dataclass

from ..ports import EndpointRepositoryPort, RouteCatalogPort


@dataclass(frozen=True, slots=True)
class EndpointRegistrySyncResult:
    discovered: int
    created: int
    removed: int


class EndpointRegistrySyncService:
    def __init__(self, *, endpoints: EndpointRepositoryPort, route_catalog: RouteCatalogPort):
        self.endpoints = endpoints
        self.route_catalog = route_catalog

    async def sync_registered_endpoints(self):
        discovered_routes = self.route_catalog.list_routes()
        discovered_keys = {
            (route["endpoint"], route["method"])
            for route in discovered_routes
        }
        existing_keys = await self.endpoints.list_keys()

        missing_keys = discovered_keys - existing_keys
        stale_keys = existing_keys - discovered_keys

        created_count = 0
        for endpoint, method in sorted(missing_keys):
            await self.endpoints.create(endpoint=endpoint, method=method)
            created_count += 1

        removed_count = await self.endpoints.delete_by_keys(stale_keys)
        return EndpointRegistrySyncResult(
            discovered=len(discovered_keys),
            created=created_count,
            removed=removed_count,
        )
