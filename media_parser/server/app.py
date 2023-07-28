from fastapi import APIRouter, FastAPI

from ..server.sentry import sentry_init
from ..settings import settings

sentry_init()

app = FastAPI(
    title=settings.name,
    description=settings.description,
    version=settings.version,
)

api = APIRouter(prefix="/api/v1")
