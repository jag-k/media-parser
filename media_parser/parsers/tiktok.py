import asyncio
import logging
import re
from re import Match
from typing import Literal

import aiohttp
from aiohttp import ClientSession
from pydantic import BaseModel, Field

from media_parser.context import MAX_SIZE
from media_parser.models import Image, Media, ParserType, Video
from media_parser.utils import generate_timer

from .base import BaseParser as BaseParser
from .base import MediaCache

logger = logging.getLogger(__name__)

TT_USER_AGENT = (
    "com.ss.android.ugc.trill/494+Mozilla/5.0+(Linux;+Android+12;+2112123G+Build/SKQ1.211006.001;+wv)"
    "+AppleWebKit/537.36+(KHTML,+like+Gecko)+Version/4.0+Chrome/107.0.5304.105+Mobile+Safari/537.36"
)

time_it = generate_timer(logger)


class TiktokParser(BaseParser, BaseModel, type=ParserType.TIKTOK):
    user_agent: str = Field(default=TT_USER_AGENT)

    def reg_exps(self):
        return [
            # https://www.tiktok.com/t/ZS8s7cPmd/
            re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/(?P<short_suffix>\w+)/(?P<id>\w+)/?"),
            # https://vt.tiktok.com/ZSRq1jcrg/
            # https://vm.tiktok.com/ZSRq1jcrg/
            re.compile(r"(?:https?://)?(?:(?P<domain>[a-z]{2})\.)?tiktok\.com/(?P<id>\w+)/?"),
            # https://www.tiktok.com/@thejoyegg/video/7136001098841591041
            re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/@(?P<author>\w+)/video/(?P<video_id>\d+)/?"),
        ]

    def _is_supported(self) -> bool:
        return True

    async def _parse(
        self,
        session: aiohttp.ClientSession,
        match: Match,
        cache: MediaCache,
    ) -> list[Media]:
        m = match.groupdict({})
        author: str
        if "short_suffix" in m:
            suffix = m["short_suffix"]
            url_id = m["id"]
            original_url = f"https://www.tiktok.com/{suffix}/{url_id}"
            logger.info("Get video id from: %s", original_url)
            video_location = await self._get_video_id(original_url)
            if video_location is None:
                return []
            author, video_id = video_location

        elif "id" in m:
            url_id = m.get("id")
            domain = m.get("domain", "vt")
            original_url = f"https://{domain}.tiktok.com/{url_id}"
            logger.info("Get video id from: %s", original_url)
            video_location = await self._get_video_id(original_url)
            if video_location is None:
                return []
            author, video_id = video_location

        else:
            author = str(m.get("author", "")).lower()
            video_id: int = int(m.get("video_id"))
            original_url = f"https://www.tiktok.com/@{author}/video/{video_id}"

        await cache.find_by_original_url(original_url)

        logger.info(
            "Getting video link from: %s (video_id=%d)",
            original_url,
            video_id,
        )

        try:
            with time_it("tiktok_get_video_data"):
                data: dict = await self._get_video_data(video_id)

        except Exception as e:
            logger.exception(
                "Error while getting video data: %s",
                original_url,
                exc_info=e,
            )
            return []

        real_author = data.get("author", {}).get("unique_id", "").lower()
        if author and author != real_author:
            logger.info(
                "Author mismatch: %s != %s",
                author,
                real_author,
            )
            return []

        media_type: Literal["video", "image", None] = data.get("type", None)
        logger.info("Media type: %s", media_type)

        with time_it("process_video"):
            if media_type == "video":
                return await cache.save_group(self._process_video(data, original_url))

            elif media_type == "image":
                return await cache.save_group(self._process_image(data, original_url))
        return []

    def _process_video(self, data: dict, original_url: str) -> list[Video]:
        max_quality_url = data.get("video_data", {}).get("nwm_video_url_HQ")

        try:
            max_size = float(MAX_SIZE.get("inf"))
        except ValueError:
            max_size = float("inf")

        try:
            url: str | None = max(
                filter(
                    lambda x: x.get("data_size", 0) <= max_size,
                    (x.get("play_addr", {}) for x in data.get("video", {}).get("bit_rate", [])),
                ),
                key=lambda x: x.get("data_size", 0),
            ).get("url_list", [None])[0]
        except ValueError:
            url = None

        if not url:
            logger.info("No url in response")
            return []

        caption: str | None = data.get("desc", None)
        thumbnail_url: str | None = data.get("cover_data", {}).get("origin_cover", {}).get("url_list", [None])[0]
        nickname: str | None = data.get("author", {}).get("nickname", None)
        language: str | None = data.get("region", None)

        video = Video(
            url=url,
            type=self.TYPE,
            caption=caption,
            thumbnail_url=thumbnail_url,
            author=nickname,
            original_url=original_url,
            language=language,
            max_quality_url=max_quality_url,
        )
        if video:
            return [video]
        return []

    def _process_image(self, data: dict, original_url: str) -> list[Image]:
        info = data.get("image_post_info", {})

        caption: str | None = data.get("desc", None)
        thumbnail_url: str | None = info.get("image_post_info", {}).get("thumbnail", {}).get("url_list", [None])[-1]
        nickname: str | None = data.get("author", {}).get("nickname", None)
        language: str | None = data.get("region", None)

        return [
            Image(
                type=self.TYPE,
                original_url=original_url,
                url=img.get("url_list", [None])[-1],
                caption=caption,
                thumbnail_url=thumbnail_url,
                language=language,
                height=img.get("height", None),
                width=img.get("height", None),
                author=nickname,
            )
            for images in info.get("images", [])
            if (img := images.get("display_image", {}))
        ]

    @classmethod
    async def _get_video_id(cls, url: str) -> tuple[str, int] | None:
        counter = 0
        async with ClientSession() as session:
            while "@" not in url and counter < 5:
                async with session.get(url, allow_redirects=False) as resp:
                    url = resp.headers.get("Location", "").split("?", 1)[0]
                    if url.startswith("/"):
                        url = "https://www.tiktok.com" + url
                    counter += 1
        base = url.rsplit("/", 1)[-1]
        author = url.split("@", 1)[-1].split("/", 1)[0]
        if not base or not base.isdigit():
            return None
        return author, int(base)

    @staticmethod
    async def _get_video_data(video_id: int) -> dict:
        async with ClientSession(
            headers={
                "Accept": "application/json",
                "User-Agent": TT_USER_AGENT,
            }
        ) as session:
            async with session.get(
                "https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/",
                params={
                    "aweme_id": video_id,
                },
            ) as resp:
                raw_data: dict = await resp.json()
            if not raw_data:
                logger.error("Empty response with %r", resp.url)
                return {}
        if not raw_data.get("aweme_list", []):
            logger.info("No aweme_list in response")
            return {}
        data = raw_data["aweme_list"][0]
        url_type_code = data["aweme_type"]
        url_type_code_dict = {
            0: "video",
            51: "video",
            55: "video",
            58: "video",
            61: "video",
            150: "image",
        }
        url_type = url_type_code_dict.get(url_type_code, "video")

        api_data = {
            "type": url_type,
            "aweme_id": video_id,
            "cover_data": {
                "cover": data["video"]["cover"],
                "origin_cover": data["video"]["origin_cover"],
                "dynamic_cover": (data["video"]["dynamic_cover"] if url_type == "video" else None),
            },
            "hashtags": data.pop("text_extra"),
        }

        if url_type == "video":
            wm_video = data["video"]["download_addr"]["url_list"][0]
            api_data["video_data"] = {
                "wm_video_url": wm_video,
                "wm_video_url_HQ": wm_video,
                "nwm_video_url": (data["video"]["play_addr"]["url_list"][0]),
                "nwm_video_url_HQ": (data["video"]["bit_rate"][0]["play_addr"]["url_list"][0]),
            }

        elif url_type == "image":
            no_watermark_image_list = []
            watermark_image_list = []

            for i in data["image_post_info"]["images"]:
                no_watermark_image_list.append(i["display_image"]["url_list"][0])

                watermark_image_list.append(i["owner_watermark_image"]["url_list"][0])

            api_data["image_data"] = {
                "no_watermark_image_list": no_watermark_image_list,
                "watermark_image_list": watermark_image_list,
            }
        return data | api_data


if __name__ == "__main__":

    async def main():
        parser = TiktokParser()
        async with ClientSession() as session:
            print(
                await parser.parse(
                    session,
                    "https://vm.tiktok.com/ZMYQFQBQ9/",
                )
            )

    asyncio.run(main())
