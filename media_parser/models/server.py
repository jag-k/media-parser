from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from .medias import GroupedMedia, ParserType

__all__ = (
    "StatusResponse",
    "ParserStatus",
    "ParserStatusResponse",
    "ParseRequest",
    "FeedbackTypes",
    "FeedbackRequest",
    "FeedbackResponse",
)


class MediaNotFoundReasons(BaseModel):
    type: str
    message: str


class MediaNotFoundReason(Enum):
    not_matched = MediaNotFoundReasons(type="not_matched", message="Media not matched on any parser")
    service_response_empty = MediaNotFoundReasons(type="service_response_empty", message="Service(s) response empty")

    def make_exc(self) -> "MediaNotFoundError":
        return MediaNotFoundError(MediaNotFoundResponse(error=self))


class MediaNotFoundResponse(BaseModel):
    status: Literal["error"] = "error"
    error: MediaNotFoundReason


class MediaNotFoundError(Exception):
    def __init__(self, response: MediaNotFoundResponse):
        self.response = response
        super().__init__(response.error.value.message)


class GroupedMediaResponse(BaseModel):
    status: Literal["ok"] = "ok"
    result: GroupedMedia = Field(default_factory=GroupedMedia)


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
