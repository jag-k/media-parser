import asyncio
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from re import Match, Pattern
from typing import Any, ClassVar, Required, Self, TypedDict

import aiohttp
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, ConfigDict

from media_parser.database import GroupedMediaModel, MongoModelController
from media_parser.models import Media, ParserType
from media_parser.utils import generate_timer

logger = logging.getLogger(__name__)
time_it = generate_timer(logger)


class MediaCache:
    def __init__(self, cache_collection: AsyncIOMotorCollection | None = None):
        self.controller: MongoModelController[str, GroupedMediaModel] | None = None
        if cache_collection:
            self.controller = GroupedMediaModel.controller(collection=cache_collection)

    class FoundCache(Exception):  # noqa: N818
        def __init__(self, medias: list[Media], original_url: str, *args) -> None:
            super().__init__(medias, original_url, *args)
            self.medias = medias
            self.original_url = original_url

    async def find_by_original_url(self, original_url: str | None = None) -> None:
        if not self.controller or not original_url:
            return
        data: GroupedMediaModel | None = await self.controller.find(original_url)
        if data:
            raise self.FoundCache(
                medias=data.flat(),
                original_url=original_url,
            )

    async def save(self, media: Media) -> Media:
        return (await self.save_group([media]))[0]

    async def save_group(self, medias: list[Media]) -> list[Media]:
        if not self.controller:
            return medias
        grouped_media = GroupedMediaModel.from_medias(medias)
        res = await self.controller.save(grouped_media)
        logger.info("Saved %d item(s) to cache for %s", len(medias), res)
        return medias


class BaseParserConfig(TypedDict):
    type: Required[ParserType]


class BaseParser(ABC):
    TYPE: ClassVar[ParserType]

    def __init__(self, *args, config: dict[str, dict[str, Any]] | None = None, **kwargs):
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
        cache_collection: AsyncIOMotorCollection | None = None,
    ) -> list[Media]:
        start_time = time.time()
        cache = MediaCache(cache_collection=cache_collection)

        gather = [
            _get_media(session, parser, match, cache)
            for parser in self.parsers
            for reg_exp in parser.reg_exps()
            if (match := reg_exp.match(string))
        ]

        with time_it("parsing"):
            result: list[Media] = [j for i in await asyncio.gather(*gather) for j in i if j]

        logger.info(
            "Parsed %d items in %.4f seconds",
            len(result),
            time.time() - start_time,
        )
        return result

    def __init_subclass__(cls, **kwargs: BaseParserConfig):
        super().__init_subclass__()
        t: ParserType | None = kwargs.get("type", None)
        if not t:
            raise ValueError("type is required")

        cls.TYPE = t
        cls.__doc__ = "Parser for " + str(t.value)

    @classmethod
    def generate_schema(cls):
        import jsonref

        class ParserSchema(BaseModel):
            model_config = ConfigDict(extra="allow")
            __annotations__ = {parser.TYPE.value.lower(): parser for parser in cls.__subclasses__()}

        schema = dict(jsonref.loads(ParserSchema.schema_json()))
        schema.pop("$defs", None)
        schema.pop("required", None)
        return json.dumps(schema, indent=2, ensure_ascii=False)

    def __str__(self):
        return f"<{self.__class__.__name__} {self.TYPE.value}>"


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
