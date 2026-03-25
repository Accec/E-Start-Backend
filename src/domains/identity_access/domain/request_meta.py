from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestMeta:
    api: str
    ip: str
    ua: str
