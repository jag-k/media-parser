import asyncio
import json
import logging
import re
from re import Match, Pattern

import aiohttp
from pydantic import BaseModel, Field

from media_parser.models import Media, ParserType, Video

from .base import BaseParser as BaseParser
from .base import MediaCache

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"


class InstagramParser(BaseParser, BaseModel, type=ParserType.INSTAGRAM):
    instagram_saas_token: str | None = Field(default=None, description="Set this for enable instagram proxy")
    instagram_saas_api: str = Field(
        default="https://api.lamadava.com", description="Set this to change instagram saas api"
    )
    user_agent: str = Field(default=USER_AGENT, description="Set this to change user agent")

    def reg_exps(self) -> list[Pattern[str]]:
        return [
            # https://www.instagram.com/p/CTQZ5Y8J8ZU/
            # https://www.instagram.com/reel/CTQZ5Y8J8ZU/
            # https://instagram.com/reel/CqQGB-1ISIw/
            re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/(?P<type>\w+)/(?P<id>[\w-]+)"),
        ]

    def _is_supported(self) -> bool:
        return True

    async def _parse(
        self,
        session: aiohttp.ClientSession,
        match: Match,
        cache: MediaCache,
    ) -> list[Media]:
        post_id = match.group("id")
        post_type = match.group("type")

        original_url = f"https://www.instagram.com/{post_type}/{post_id}"

        await cache.find_by_original_url(original_url)

        variables = {
            "shortcode": post_id,
            "child_comment_count": 3,
            "fetch_comment_count": 40,
            "parent_comment_count": 24,
            "has_threaded_comments": False,
        }

        params = {
            "query_hash": "477b65a610463740ccdb83135b2014db",
            "variables": json.dumps(variables, separators=(",", ":")),
        }

        async with session.get(
            "https://www.instagram.com/graphql/query/",
            params=params,
            headers={"User-Agent": self.user_agent},
        ) as response:
            data: dict = await response.json()

        if data.get("status") == "fail" and self.instagram_saas_token:
            return await self.get_media_from_saas(
                session=session,
                cache=cache,
                media_code=post_id,
                original_url=original_url,
            )

        logger.info("Got data: %s", data)
        shortcode_media = data.get("data", {}).get("shortcode_media") or {}

        if not shortcode_media.get("is_video", False):
            logger.info("%s is not a video", original_url)
            return []
        caption = shortcode_media.get("title", None)
        if not caption:
            caption = " ".join(
                [
                    node.get("node", {}).get("text", "")
                    for node in shortcode_media.get("edge_media_to_caption", {}).get("edges", [])
                ]
            ).strip()
        url: str | None = shortcode_media.get("video_url", None)
        if not url:
            return []

        thumbnail_url = shortcode_media.get("display_url", None)

        video = Video(
            caption=caption or None,
            type=self.TYPE,
            original_url=original_url,
            thumbnail_url=thumbnail_url,
            author=shortcode_media.get("owner", {}).get("username", None),
            url=url,
            mime_type="video/mp4",
            width=shortcode_media.get("dimensions", {}).get("width", None),
            height=shortcode_media.get("dimensions", {}).get("height", None),
            duration=int(shortcode_media.get("video_duration", "0")) or None,
        )
        return await cache.save_group([video])

    async def get_media_from_saas(
        self,
        session: aiohttp.ClientSession,
        cache: MediaCache,
        media_code: str,
        original_url: str,
    ) -> list[Media]:
        if not self.instagram_saas_token:
            return []
        logger.info("Using instagram saas for %r", original_url)

        async with session.get(
            f"{self.instagram_saas_api}/v1/media/by/code",
            params={"code": media_code},
            headers={"x-access-key": self.instagram_saas_token},
        ) as resp:
            if resp.status != 200:
                logger.error("Error: %s %s", resp.status, await resp.text())
                return []
            data: dict = await resp.json()

        logger.info("Got data: %s", data)
        if not data:
            return []

        url: str | None = data.get("video_url", None)
        if not url:
            logger.info("%s is not a video", original_url)
            return []

        caption = data.get("title", None) or data.get("caption_text", None)

        thumbnail_url = data.get("thumbnail_url", None)
        video_meta = data.get("video_versions", [{}])[0]
        video = Video(
            caption=caption or None,
            type=self.TYPE,
            original_url=original_url,
            thumbnail_url=thumbnail_url,
            author=data.get("user", {}).get("username", None),
            url=url,
            mime_type="video/mp4",
            width=video_meta.get("width", None),
            height=video_meta.get("height", None),
            duration=int(data.get("video_duration", 0)) or None,
        )
        return await cache.save_group([video])


if __name__ == "__main__":

    async def main():
        async with aiohttp.ClientSession() as session:
            print(
                await InstagramParser().parse(
                    session,
                    "https://instagram.com/reel/CqQGB-1ISIw/",
                )
            )

    asyncio.run(main())
