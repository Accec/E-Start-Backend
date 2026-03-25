import logging
from typing import Any

from sanic.request import Request

from core.constants import API_LOGGER


logger = logging.getLogger(API_LOGGER)
MAX_LOGGED_PAYLOAD_LENGTH = 2048


def resolve_request_path(request: Request) -> str:
    return request.uri_template or request.path


def normalize_request_mapping(mapping: Any) -> dict[str, Any]:
    if mapping is None:
        return {}

    normalized: dict[str, Any] = {}
    for key in mapping.keys():
        if hasattr(mapping, "getlist"):
            values = mapping.getlist(key)
            normalized[key] = values if len(values) > 1 else values[0]
            continue
        normalized[key] = mapping.get(key)
    return normalized


def extract_request_payload(request: Request) -> dict[str, Any]:
    if request.method in {"GET", "DELETE"}:
        return normalize_request_mapping(request.args)

    content_type = (request.content_type or "").lower()
    if "application/json" in content_type:
        payload = request.json
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return payload
        return {"data": payload}

    return normalize_request_mapping(request.form)


def format_request_payload(payload: dict[str, Any]) -> str:
    serialized = repr(payload)
    if len(serialized) <= MAX_LOGGED_PAYLOAD_LENGTH:
        return serialized
    return f"{serialized[:MAX_LOGGED_PAYLOAD_LENGTH]}...<truncated>"


async def request_handling(request: Request):
    request.ctx.request_id = request.id
    request.ctx.real_ip = request.remote_addr or request.ip
    request.ctx.ua = request.headers.get("user-agent", "")
    # Use a single normalized route key so auth, rate limiting, and audit logs
    # all talk about the same endpoint identifier.
    request.ctx.request_path = resolve_request_path(request)

    try:
        request_payload = extract_request_payload(request)
    except Exception as exc:
        logger.warning(
            "request_id[%s]-client_ip[%s]-url[%s]-payload_extract_failed[%s]",
            request.ctx.request_id,
            request.ctx.real_ip,
            request.url,
            exc,
        )
        return

    if request_payload:
        logger.info(
            "request_id[%s]-client_ip[%s]-url[%s]-body[%s]",
            request.ctx.request_id,
            request.ctx.real_ip,
            request.url,
            format_request_payload(request_payload),
        )
