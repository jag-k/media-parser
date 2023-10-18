from fastapi import APIRouter, FastAPI
from fastapi.responses import Response

from ..models.server import MediaNotFoundError
from ..settings import settings
from .sentry import sentry_init

sentry_init()

app = FastAPI(
    title=settings.name,
    description=settings.description,
    version=settings.version,
)

api = APIRouter(prefix="/api/v1")


@app.exception_handler(MediaNotFoundError)
def media_not_found_exception_handler(_, exc: MediaNotFoundError):
    return Response(
        content=exc.response.json(),
        status_code=404,
        media_type="application/json",
    )
