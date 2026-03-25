from dataclasses import dataclass
from typing import TYPE_CHECKING, Awaitable, Callable

from tortoise import Tortoise

from core.http import http_response
from core.responses import ServiceUnavailableError, Success

if TYPE_CHECKING:
    from app.bootstrap.container import ApplicationBootstrap


ReadinessCheck = Callable[[], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class ReadinessProbe:
    name: str
    check: ReadinessCheck


@dataclass(slots=True)
class HealthController:
    app_name: str
    readiness_probes: tuple[ReadinessProbe, ...]

    async def health(self, request):
        return http_response(
            Success.code,
            Success.msg,
            result={
                "app": self.app_name,
                "status": "alive",
            },
        )

    async def ready(self, request):
        dependencies: dict[str, str] = {}
        ready = True

        # Fail readiness as soon as an external dependency is unhealthy so
        # orchestration can stop routing traffic to this instance.
        for probe in self.readiness_probes:
            try:
                await probe.check()
            except Exception as exc:
                ready = False
                dependencies[probe.name] = str(exc)
            else:
                dependencies[probe.name] = "ok"

        if ready:
            return http_response(
                Success.code,
                Success.msg,
                result={
                    "app": self.app_name,
                    "status": "ready",
                    "dependencies": dependencies,
                },
            )

        return http_response(
            ServiceUnavailableError.code,
            ServiceUnavailableError.msg,
            result={
                "app": self.app_name,
                "status": "degraded",
                "dependencies": dependencies,
            },
            status=503,
        )


async def check_database_readiness():
    connection = Tortoise.get_connection("default")
    await connection.execute_query("SELECT 1")


def build_redis_readiness_check(redis_client):
    async def check():
        await redis_client.ping()

    return check


def register_health_routes(system_blueprint, bootstrap: "ApplicationBootstrap"):
    from app.bootstrap.routing import add_route

    controller = HealthController(
        app_name=bootstrap.config.app,
        readiness_probes=(
            ReadinessProbe(name="database", check=check_database_readiness),
            ReadinessProbe(name="redis", check=build_redis_readiness_check(bootstrap.identity_access.redis_client)),
        ),
    )

    add_route(system_blueprint, "/health", methods=["GET"], handler=controller.health)
    add_route(system_blueprint, "/ready", methods=["GET"], handler=controller.ready)
