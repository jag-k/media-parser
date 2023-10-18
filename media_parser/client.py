import httpx
from pydantic import AnyHttpUrl, BaseModel, Field

from .models import FeedbackTypes, ParserStatus
from .models.medias import GroupedMediaResult, ParserType

__all__ = ("Client",)


class Client(BaseModel):
    """
    Client for media-parser

    :param url: URL to media-parser
    :param service: Service name (used for feedback)
    """

    url: AnyHttpUrl
    service: str | None = Field(None, description="X-Service in request")
    timeout: int = Field(4, description="Timeout for requests")

    @property
    def client(self):
        return httpx.AsyncClient(base_url=self.url, timeout=self.timeout)

    async def parse(self, url: str, use_cache: bool = True, user: str | None = None) -> GroupedMediaResult:
        """
        Parse media from url

        :param url: URL to parse
        :param use_cache: Use cache on server
        :param user: Username (used for feedback)

        :return: GroupedMedia
        """

        headers = {}
        if self.service:
            headers["X-Service"] = self.service

        if user:
            headers["X-User"] = str(user)

        response = await self.client.post(
            "/api/v1/parse",
            json={
                "url": url,
                "use_cache": use_cache,
            },
            headers=headers,
            timeout=self.timeout,
        )
        if response.status_code not in (200, 404):
            raise response.raise_for_status()

        event_id: str | None = response.headers.get("X-Sentry-EventID", None)
        resp = response.json().get("result", {})
        result = GroupedMediaResult.parse_obj(resp)
        print(f"{result=}")
        result.event_id = event_id
        result.request_url = url
        return result

    async def parsers(self) -> list[ParserStatus]:
        """
        Get a list of available parsers

        :return: List of parsers statuses
        """

        headers = {}
        if self.service:
            headers["X-Service"] = self.service

        response = await self.client.get(
            "/api/v1/parsers",
            headers=headers,
        )
        response.raise_for_status()
        return [ParserStatus.parse_obj(parser) for parser in response.json().get("statuses", [])]

    async def enabled_parsers(self) -> list[ParserType]:
        """
        Get a list of enabled parsers

        :return: List of enabled parsers
        """

        parsers = await self.parsers()
        return [parser.parser_type for parser in parsers if parser.enabled]

    async def send_feedback(self, media: GroupedMediaResult, user: str, feedback_type: FeedbackTypes):
        """
        Send feedback to media-parser

        Its work only if sentry enabled

        :param media: Media
        :param user: Username
        :param feedback_type: Feedback type
        """

        headers = {}
        if self.service:
            headers["X-Service"] = self.service

        if user:
            headers["X-User"] = user

        response = await self.client.post(
            "/api/v1/feedback",
            data={
                "event_id": media.event_id,
                "username": user,
                "feedback_type": feedback_type,
                "request_url": media.request_url,
            },
            headers=headers,
        )
        response.raise_for_status()
        return response
