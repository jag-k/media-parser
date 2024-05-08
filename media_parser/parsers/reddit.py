import logging
import re
from re import Match, Pattern
from urllib.parse import urlparse

import aiohttp
from aiohttp import InvalidURL
from pydantic import BaseModel, Field

from media_parser.models import Media, ParserType, Video

from .base import BaseParser as BaseParser
from .base import MediaCache

logger = logging.getLogger(__name__)


class RedditParser(BaseParser, BaseModel, type=ParserType.REDDIT):
    user_agent: str | None = Field("video downloader (by u/Jag_k)", description="User agent for Reddit API")
    client_id: str = Field(..., description="Client ID for Reddit API")
    client_secret: str = Field(..., description="Client secret for Reddit API")

    def reg_exps(self) -> list[Pattern[str]]:
        return [
            # redd.it/2gmzqe
            re.compile(r"(?:https?://)?(?:www\.)?redd\.it/(?P<id>\w+)"),
            # reddit.com/comments/2gmzqe/
            # www.reddit.com/r/redditdev/comments/2gmzqe/praw_https/
            # www.reddit.com/gallery/2gmzqe
            re.compile(r"(?:https?://)?(?:www\.)?reddit\.com/(?P<link>[\w/]+)"),
        ]

    def _is_supported(self) -> bool:
        return bool(self.user_agent and self.client_id and self.client_secret)

    @property
    def auth(self):
        return aiohttp.BasicAuth(
            self.client_id,
            self.client_secret,
        )

    async def _parse(
        self,
        session: aiohttp.ClientSession,
        match: Match,
        cache: MediaCache,
    ) -> list[Media]:
        try:
            comment_id = match.group("id")
        except (IndexError, InvalidURL):
            try:
                comment_id = id_from_url(f"https://reddit.com/{match.group('link')}")
            except (IndexError, InvalidURL):
                return []

        original_url = f"https://redd.it/{comment_id}"

        await cache.find_by_original_url(original_url)

        logger.info("Getting video link from: %s", original_url)
        cmt = await comment(session, comment_id)
        media = cmt.get("media", {})
        if not media:
            logger.info("No media found")
            return []

        video_url = media.get("reddit_video", {}).get("fallback_url", "").rstrip("?source=fallback")
        if not video_url:
            logger.info("No video found")
            return []

        author = cmt.get("author")
        title = cmt.get("title")
        subreddit = cmt.get("subreddit")

        thumbnail = cmt.get("thumbnail")
        if cmt.get("preview", {}).get("enabled", False):
            thumbnail = cmt["preview"]["images"][0]["source"]["url"]

        # TODO: Get video with audio
        return await cache.save_group(
            [
                Video(
                    original_url=original_url,
                    author=author,
                    caption=title,
                    thumbnail_url=thumbnail,
                    type=ParserType.REDDIT,
                    extra_description=f"by u/{author} in r/{subreddit}",
                    url=video_url,
                )
            ]
        )


async def comment(session: aiohttp.ClientSession, comment_id: str, reddit_parser: RedditParser) -> dict:
    async with session.get(
        f"https://api.reddit.com/comments/{comment_id}",
        auth=reddit_parser.auth,
        headers={"User-Agent": reddit_parser.user_agent},
    ) as resp:
        data = await resp.json()
    return data[0].get("data", {}).get("children", [{}])[0].get("data", {})


def id_from_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.netloc:
        raise InvalidURL(url)
    parts = parsed.path.rstrip("/").split("/")

    if "comments" not in parts and "gallery" not in parts:
        submission_id = parts[-1]
        if "r" in parts:
            # Invalid URL (subreddit, not submission)
            raise InvalidURL(url)

    elif "gallery" in parts:
        submission_id = parts[parts.index("gallery") + 1]

    elif parts[-1] == "comments":
        # Invalid URL (submission ID not present)
        raise InvalidURL(url)

    else:
        submission_id = parts[parts.index("comments") + 1]

    if not submission_id.isalnum():
        raise InvalidURL(url)
    return submission_id
