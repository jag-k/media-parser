import json

import aiohttp
import sentry_sdk

from context import SERVICE
from models import (
    FeedbackRequest,
    FeedbackResponse,
    GroupedMedia,
    ParseRequest,
    ParserStatus,
    ParserStatusResponse,
    StatusResponse,
)
from parsers import BaseParser
from server.app import api
from server.sentry import send_feedback
from settings import PARSERS_PATH, sentry_settings
from utils import Timer

with PARSERS_PATH.open("r", encoding="utf-8") as f:
    PARSER = BaseParser(config=json.load(f))


@api.get("/health")
async def health() -> StatusResponse:
    return StatusResponse(status="ok")


@api.get("/parsers")
async def parser_status() -> ParserStatusResponse:
    return ParserStatusResponse(
        statuses=[
            ParserStatus(
                parser_type=k,
                enabled=v,
            )
            for k, v in PARSER.supported().items()
        ]
    )


@api.post("/parse")
async def parse(data: ParseRequest) -> GroupedMedia:
    with sentry_sdk.start_transaction(name="Parce", op="parce", description="Parsing") as t:
        with Timer("total_parce_time", transaction=t):
            async with aiohttp.ClientSession() as session:
                return GroupedMedia.from_medias(
                    await PARSER.parse(
                        session,
                        data.url,
                        use_cache=data.use_cache,
                    )
                )


@api.post("/feedback")
async def feedback(data: FeedbackRequest) -> FeedbackResponse:
    try:
        if sentry_settings.feedback_enabled:
            service: str = SERVICE.get("none")

            await send_feedback(
                name=data.username,
                email=f"{service}@jagk.dev",
                comments=data.feedback_type.value,
                event_id=data.event_id,
            )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return FeedbackResponse(
            status="error",
            sentry_enabled=sentry_settings.feedback_enabled,
        )

    return FeedbackResponse(
        status="ok",
        sentry_enabled=sentry_settings.feedback_enabled,
    )
