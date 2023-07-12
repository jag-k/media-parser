import sentry_sdk
from context import context_vars, get_context_vars
from fastapi import Request, Response

from .app import app


@app.middleware("http")
async def sentry_middleware(request: Request, call_next):
    c_vars = get_context_vars()
    sentry_sdk.set_context("Context Vars", c_vars)
    for value in context_vars.values():
        sentry_sdk.set_tag(f"context.{value.name}", value)

    service = c_vars.get("SERVICE", None)
    sentry_sdk.set_tag("service", service)

    user = c_vars.get("USER", None)

    sentry_user = None
    if user:
        sentry_user = {"id": user, "username": user}
        if service:
            sentry_user["email"] = f"{service}@jagk.dev"

    elif service:
        sentry_user = {"id": service, "username": service}

    sentry_sdk.set_user(sentry_user)
    resp: Response = await call_next(request)
    resp.headers.setdefault("X-Sentry-EventID", sentry_sdk.last_event_id())
    return resp


@app.middleware("http")
async def context_vars_middleware(request: Request, call_next):
    tokens = {name: value.set(request.headers.get(f"X-{name}".lower(), None)) for name, value in context_vars.items()}
    try:
        return await call_next(request)
    finally:
        for name, value in tokens.items():
            context_vars[name].reset(value)
