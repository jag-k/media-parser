import logging
import re
from re import Match

import aiohttp
from pydantic import BaseModel, Field

from media_parser.models import Media, ParserType, Video

from .base import BaseParser as BaseParser
from .base import MediaCache

logger = logging.getLogger(__name__)

# https://twitter.com/Yoda4ever/status/1580609309217628160
TWITTER_RE = re.compile(r"(?:https?://)?(?:www\.)?twitter\.com/(?P<user>\w+)/status/(?P<id>\d+)")
# https://x.com/Yoda4ever/status/1580609309217628160
X_RE = re.compile(r"(?:https?://)?(?:www\.)?x\.com/(?P<user>\w+)/status/(?P<id>\d+)")


class TwitterParser(BaseParser, BaseModel, type=ParserType.TWITTER):
    twitter_bearer_token: str = Field(..., description="Bearer token for Twitter API")

    def reg_exps(self):
        return [
            TWITTER_RE,
            X_RE,
            # https://t.co/sOHvySZwUo
            re.compile(r"(?:https?://)?t\.co/(?P<tco_id>\w+)"),
        ]

    def _is_supported(self) -> bool:
        return bool(self.twitter_bearer_token)

    async def _parse(
        self,
        session: aiohttp.ClientSession,
        match: Match,
        cache: MediaCache,
    ) -> list[Media]:
        try:
            tweet_id = match.group("id")
        except IndexError:
            try:
                tco_id = match.group("tco_id")
            except IndexError:
                return []
            async with session.get(f"https://t.co/{tco_id}") as response:
                new_match = TWITTER_RE.match(str(response.real_url))
            return await self._parse(session, new_match, cache)

        original_url = f"https://twitter.com/i/status/{tweet_id}"

        await cache.find_by_original_url(original_url)

        logger.info("Getting video link from: %s", original_url)

        async with session.get(
            f"https://api.twitter.com/2/tweets/{tweet_id}",
            params={
                "media.fields": "type,variants",
                "expansions": "attachments.media_keys,author_id",
                "user.fields": "username",
            },
            headers={"Authorization": f"Bearer {self.twitter_bearer_token}"},
        ) as response:
            data: dict = await response.json()

        logger.debug("Got data: %s", data)
        includes = data.get("includes", {})
        medias = includes.get("media", [])
        author = includes.get("users", [{}])[0].get("username", None)
        caption = data.get("data", {}).get("text", None)

        result = []
        for media in medias:
            if media.get("type") == "video":
                thumbnail_url = media.get("preview_image_url")
                result.append(
                    Video(
                        url=max(
                            media.get("variants", []),
                            key=lambda x: x.get("bit_rate", 0),
                        ).get("url"),
                        caption=caption,
                        thumbnail_url=thumbnail_url,
                        type=ParserType.TWITTER,
                        author=author,
                        original_url=original_url,
                    )
                )
        return await cache.save_group(result)
