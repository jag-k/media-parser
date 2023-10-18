import httpx
import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.pure_eval import PureEvalIntegration
from sentry_sdk.integrations.pymongo import PyMongoIntegration
from sentry_sdk.integrations.stdlib import StdlibIntegration

from ..settings import BASE_PATH, sentry_settings, settings


def sentry_init():
    if not sentry_settings.enabled:
        return
    sentry_sdk.init(
        dsn=sentry_settings.dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        project_root=str(BASE_PATH),
        environment=sentry_settings.environment or "dev",
        max_breadcrumbs=50,
        debug=True,
        release=f"{settings.name}@{settings.version}",
        include_local_variables=True,
        integrations=[
            PureEvalIntegration(),
            HttpxIntegration(),
            PyMongoIntegration(),
            AsyncioIntegration(),
            LoggingIntegration(),
            StdlibIntegration(),
        ],
    )


def send_feedback(name: str, email: str, comments: str, event_id: str | None = None):
    if not sentry_settings.feedback_enabled:
        return False

    if not event_id:
        event_id = sentry_sdk.last_event_id()

    url = (
        f"{sentry_settings.api_host}/api/0/projects/{sentry_settings.organisation_slug}/{sentry_settings.project_slug}"
        f"/user-feedback/"
    )

    headers = {"Authorization": f"Bearer {sentry_settings.auth_token}"}

    data = {"event_id": event_id, "name": str(name), "email": str(email), "comments": str(comments)}

    response = httpx.post(url, headers=headers, data=data)
    return response
