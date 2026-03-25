import logging

from core.config import load_config
from core.constants import JOB_LOGGER
from domains.identity_access.application import EndpointRegistrySyncService
from domains.identity_access.infrastructure.repos import EndpointRepository
from infra.scheduler import add_interval_job
from infra.web import SanicRouteCatalog


Logger = logging.getLogger(JOB_LOGGER)
sync_service = EndpointRegistrySyncService(
    endpoints=EndpointRepository(),
    route_catalog=SanicRouteCatalog(app_name=load_config().app),
)


@add_interval_job("update_endpoint", 1 * 60 * 60 * 24)
async def update_endpoint():
    result = await sync_service.sync_registered_endpoints()
    Logger.info(
        "Endpoint registry synchronized: discovered=%s created=%s removed=%s",
        result.discovered,
        result.created,
        result.removed,
    )
