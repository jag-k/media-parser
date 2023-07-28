from contextvars import ContextVar
from typing import Any

SERVICE: ContextVar[str | None] = ContextVar("service", default=None)
USER: ContextVar[str | None] = ContextVar("user", default=None)
MAX_SIZE: ContextVar[str] = ContextVar("max-size", default="inf")  # float(str or "inf")

context_vars: dict[str, ContextVar] = {
    name: value for name, value in globals().items() if isinstance(value, ContextVar)
}


def get_context_vars() -> dict[str, Any]:
    return {name: value.get() for name, value in context_vars.items()}


def get_max_size() -> float:
    try:
        return float(MAX_SIZE.get("inf"))
    except ValueError:
        return float("inf")
