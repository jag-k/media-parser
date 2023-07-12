from fastapi import APIRouter, FastAPI

from settings import settings
from server.sentry import sentry_init

sentry_init()

app = FastAPI(
    title=settings.name,
    description=settings.description,
    version=settings.version,
)

api = APIRouter(prefix="/api/v1")
