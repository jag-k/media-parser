import asyncio
import logging
import re
import time
from abc import abstractmethod
from re import Match, Pattern
from typing import Any, Self

import aiohttp
from database import GroupedMediaModel
from models.medias import Media, ParserType
from pydantic import BaseConfig, BaseModel, Extra
from utils import generate_timer

logger = logging.getLogger(__name__)
time_it = generate_timer(logger, True)


class MediaCache:
    def __init__(self, use_cache: bool = True):
        self._use_cache = use_cache

    class FoundCache(Exception):
        def __init__(self, medias: list[Media], original_url: str, *args):
            super().__init__(medias, original_url, *args)
            self.medias = medias
            self.original_url = original_url

    async def find_by_original_url(self, original_url: str | None = None):
        if not self._use_cache or not original_url:
            return
        data = await GroupedMediaModel.find(original_url)
        if data:
            raise self.FoundCache(
                medias=data,
                original_url=original_url,
            )

    async def save(self, media: Media) -> Media:
        if not self._use_cache:
            return media
        res = await GroupedMediaModel.from_medias([media]).save()
        logger.info("Saved item to cache for %s", res)
        return media

    async def save_group(self, medias: list[Media]) -> list[Media]:
        if not self._use_cache:
            return medias
        res = await GroupedMediaModel.from_medias(medias).save()
        logger.info("Saved %d item(s) to cache for %s", len(medias), res)
        return medias


class BaseParser:
    TYPE: ParserType

    def __init__(self, *args, config: dict[str, dict[str, Any]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        if config is None:
            config = {}
        if type(self) is BaseParser:
            self._parsers: list[BaseParser] = [
                parser(**conf)
                for parser in BaseParser.__subclasses__()
                if (conf := config.get(parser.TYPE.value.lower(), None)) is not None
            ]

    def supported(self) -> dict[ParserType, bool]:
        return {parser.TYPE: parser._is_supported() for parser in self._parsers}

    @abstractmethod
    def reg_exps(self) -> list[Pattern[str]]:
        raise NotImplementedError

    @abstractmethod
    def _is_supported(self) -> bool:
        raise NotImplementedError

    @property
    def parsers(self) -> list[Self]:
        return [p for p in self._parsers if p._is_supported()]

    @abstractmethod
    async def _parse(
        self,
        session: aiohttp.ClientSession,
        match: Match,
        cache: MediaCache,
    ) -> list[Media]:
        raise NotImplementedError

    async def parse(
        self,
        session: aiohttp.ClientSession,
        string: str,
        use_cache: bool = True,
    ) -> list[Media]:
        start_time = time.time()
        cache = MediaCache(use_cache=use_cache)

        gather = [
            _get_media(session, parser, match, cache)
            for parser in self.parsers
            for reg_exp in parser.reg_exps()
            if (match := reg_exp.match(string))
        ]
        print(gather)

        with time_it("parsing"):
            result: list[Media] = [j for i in await asyncio.gather(*gather) for j in i if j]

        logger.info(
            "Parsed %d items in %.4f seconds",
            len(result),
            time.time() - start_time,
        )
        return result

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        t = kwargs.get("type", None)
        if not t:
            raise ValueError("type is required")

        cls.TYPE = t
        cls.__doc__ = "Parser for " + t.value

    @classmethod
    def generate_schema(cls):
        import json

        import jsonref

        class ParserSchema(BaseModel):
            __annotations__ = {parser.TYPE.value.lower(): parser | None for parser in cls.__subclasses__()}

            class Config(BaseConfig):
                extra = Extra.allow
                smart_union = True

        schema = dict(jsonref.loads(ParserSchema.schema_json()))
        schema.pop("definitions", None)
        return json.dumps(schema, indent=2, ensure_ascii=False)


async def _get_media(
    session: aiohttp.ClientSession,
    parser: BaseParser,
    match: re.Match[str],
    cache: MediaCache,
) -> list[Media]:
    logger.info("Found match for %s: %r", parser.TYPE, match.string)
    try:
        return await parser._parse(session, match, cache=cache)
    except MediaCache.FoundCache as e:
        logger.info("Found cache for %s", e.original_url)
        return e.medias
