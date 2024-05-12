from contextvars import ContextVar

MAX_SIZE: ContextVar[float] = ContextVar("max-size", default=float("inf"))  # float(str or "inf")
