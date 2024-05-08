from contextvars import ContextVar

MAX_SIZE: ContextVar[str] = ContextVar("max-size", default="inf")  # float(str or "inf")


def get_max_size() -> float:
    try:
        return float(MAX_SIZE.get("inf"))
    except ValueError:
        return float("inf")
