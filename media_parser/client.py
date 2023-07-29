import httpx
from pydantic import BaseModel, Field, HttpUrl

from models import FeedbackTypes
from models.medias import GroupedMedia

__all__ = ("Client",)


class Client(BaseModel):
    """
    Client for media-parser

    :param url: URL to media-parser
    :param service: Service name (used for feedback)
    """

    url: HttpUrl
    service: str | None = Field(None, description="X-Service in request")

    @property
    def client(self):
        return httpx.AsyncClient(base_url=self.url)

    async def parse(self, url: str, use_cache: bool = True, user: str | None = None) -> GroupedMedia:
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
            headers["X-User"] = user

        response = await self.client.post(
            "/api/v1/parse",
            json={
                "url": url,
                "use_cache": use_cache,
            },
            headers=headers,
        )
        response.raise_for_status()
        event_id: str | None = response.headers.get("X-Sentry-EventID", None)

        result = GroupedMedia.parse_obj(response.json())
        result.event_id = event_id
        result.request_url = url
        return result

    async def send_feedback(self, media: GroupedMedia, user: str, feedback_type: FeedbackTypes):
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
