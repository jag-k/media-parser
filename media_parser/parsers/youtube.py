import asyncio
import logging
import re
from re import Match

import aiohttp
import httpx
import pytube
from pydantic import BaseModel
from pytube import StreamQuery
from pytube.exceptions import PytubeError

from media_parser.context import get_max_size
from media_parser.models import Media, ParserType, Video

from .base import BaseParser as BaseParser
from .base import MediaCache

logger = logging.getLogger(__name__)


class YoutubeParser(BaseParser, BaseModel, type=ParserType.YOUTUBE):
    def reg_exps(self):
        return [
            # https://www.youtube.com/watch?v=TCrP1SE2DkY
            # https://youtu.be/TCrP1SE2DkY
            re.compile(r"(?:https?://)?" r"(?:" r"(?:www\.)?youtube\.com/watch\?v=" r"|youtu.be/" r")(?P<id>[\w-]+)"),
            # https://youtube.com/shorts/hBOLCcvbGHM
            # https://youtube.com/watch?v=hBOLCcvbGHM
            re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/shorts/(?P<id>[\w-]+)"),
        ]

    def _is_supported(self) -> bool:
        return True

    async def _parse(
        self,
        session: aiohttp.ClientSession,
        match: Match,
        cache: MediaCache,
    ) -> list[Media]:
        try:
            yt_id = match.group("id")
        except IndexError:
            return []

        original_url = f"https://youtube.com/watch?v={yt_id}"
        await cache.find_by_original_url(original_url)

        logger.info("Getting video link from: %s", original_url)

        loop = asyncio.get_running_loop()
        medias = await loop.run_in_executor(None, self.cpy_bound_request, original_url)

        return await cache.save_group(medias)

    def cpy_bound_request(self, original_url: str) -> list[Media]:
        yt = pytube.YouTube(original_url)
        try:
            streams_obj = StreamQuery(yt.fmt_streams)
        except KeyError:
            logger.info('No "fmt_streams" found for %r', original_url)
            return []

        streams = streams_obj.filter(type="video", progressive=True, file_extension="mp4").order_by("resolution")
        logger.info("Found %s streams", len(streams))
        stream = streams.last()
        if not stream:
            logger.info("No suitable streams found")
            return []

        max_quality_url = stream.url
        max_fs = 0

        max_size = get_max_size()

        for st in streams:
            logger.info("Stream: %s", st)
            file_size = int(httpx.head(st.url).headers.get("Content-Length", "0"))
            logger.info("Stream file size: %s", file_size)
            if max_size >= file_size > max_fs:
                logger.info("Found suitable stream with filesize %s", file_size)
                max_fs = file_size
                stream = st

        logger.info("Selected stream: %s", stream)

        try:
            return [
                Video(
                    author=yt.author,
                    caption=yt.title,
                    thumbnail_url=yt.thumbnail_url,
                    type=self.TYPE,
                    url=stream.url,
                    original_url=original_url,
                    max_quality_url=max_quality_url,
                    mime_type=stream.mime_type,
                )
            ]
        except PytubeError as err:
            logger.error("Failed to get video %r with error: %s", original_url, err)
            return []
