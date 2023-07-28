from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from .medias import ParserType


class StatusResponse(BaseModel):
    status: str = "ok"


class ParserStatus(BaseModel):
    parser_type: ParserType
    enabled: bool = False


class ParserStatusResponse(BaseModel):
    statuses: list[ParserStatus] = Field(default_factory=list)


class ParseRequest(BaseModel):
    url: HttpUrl = Field(description="URL to parse")
    use_cache: bool = Field(True, description="Use cache")


class FeedbackTypes(str, Enum):
    not_found = "not_found"
    wrong_media = "wrong_media"

    other = "other"


class FeedbackRequest(BaseModel):
    event_id: str = Field(
        title="Sentry event id", description="This value returns in response header `X-Sentry-EventID`"
    )
    username: str = Field(title="Username", description="Username of user who send feedback")
    feedback_type: FeedbackTypes = Field(FeedbackTypes.other, description="Type of feedback")
    request_url: str | None = Field(title="Request URL", description="URL of request")


class FeedbackResponse(BaseModel):
    status: Literal["ok", "error"] = "ok"
    sentry_status: bool = Field(True, description="Sentry status")
