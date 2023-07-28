import logging
import os
from pathlib import Path
from tomllib import load

from pydantic import BaseSettings

logger = logging.getLogger(__name__)

BASE_PATH = Path(__file__).parent.parent.absolute()
SRC_DIR = BASE_PATH / "media_parser"
CONFIG_DIR = Path(os.getenv("CONFIG_PATH", BASE_PATH / "config"))
CONFIG_DIR.mkdir(exist_ok=True)
PARSERS_PATH = CONFIG_DIR / "parsers.json"
PARSERS_YAML_PATH = CONFIG_DIR / "parsers.yaml"
PARSERS_YML_PATH = CONFIG_DIR / "parsers.yml"
PROJECT_TOML = BASE_PATH / "pyproject.toml"

with PROJECT_TOML.open("rb") as f:
    PROJECT_DATA = load(f)


class Config(BaseSettings.Config):
    env_file = CONFIG_DIR / ".env"
    env_file_encoding = "utf-8"


class ProjectSettings(BaseSettings):
    name: str = PROJECT_DATA["tool"]["poetry"]["name"]
    version: str = PROJECT_DATA["tool"]["poetry"]["version"]
    description: str = PROJECT_DATA["tool"]["poetry"]["description"]

    class Config(Config):
        env_prefix = "PROJECT_"


settings = ProjectSettings()


class MongoSettings(BaseSettings):
    url: str
    database: str

    class Config(Config):
        env_prefix = "MONGO_"


mongo_settings = MongoSettings()


class SentrySettings(BaseSettings):
    dsn: str | None = None
    environment: str | None = None

    organization_slug: str | None = None
    project_slug: str | None = settings.name
    auth_token: str | None = None  # with scope project:write
    api_host: str = "https://sentry.io"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("Sentry Enabled: %s", self.enabled)
        logger.info("Sentry Feedback Enabled: %s", self.feedback_enabled)

    @property
    def enabled(self) -> bool:
        return bool(self.dsn)

    @property
    def feedback_enabled(self) -> bool:
        return self.enabled and bool(self.organization_slug and self.project_slug and self.auth_token)

    class Config(Config):
        env_prefix = "SENTRY_"


sentry_settings = SentrySettings()
