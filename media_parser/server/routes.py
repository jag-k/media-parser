from collections.abc import Iterator
from typing import Annotated

import aiohttp
import sentry_sdk
from fastapi import Query, status
from starlette.responses import StreamingResponse

from ..context import SERVICE
from ..models import (
    FeedbackRequest,
    FeedbackResponse,
    GroupedMedia,
    Media,
    ParseRequest,
    ParserStatus,
    ParserStatusResponse,
    StatusResponse,
)
from ..models.server import GroupedMediaResponse, MediaNotFoundResponse
from ..parsers import create_parser
from ..settings import sentry_settings
from ..utils import Timer
from .app import api
from .sentry import send_feedback

PARSER = create_parser()


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


async def stream_media(media: Media) -> Iterator[bytes]:
    async with aiohttp.ClientSession() as session:
        async with session.get(media.url, headers=media.headers) as res:
            print(res.headers)
            async for (content, b) in res.content.iter_chunks():
                yield content


@api.post(
    "/parse",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": MediaNotFoundResponse},
        status.HTTP_202_ACCEPTED: {
            "description": "If `download` set to `true` and media is single. Returns as stream",
            "content": {
                "video/mp4": {"type": "string", "format": "binary", "example": "video.mp4", "description": "Video"},
                "video/*": {"type": "string", "format": "binary", "example": "video.webm", "description": "Video"},
                "audio/mpeg": {"type": "string", "format": "binary", "example": "audio.mp3", "description": "Audio"},
                "image/jpeg": {"type": "string", "format": "binary", "example": "image.jpg", "description": "Image"},
                "image/png": {"type": "string", "format": "binary", "example": "image.png", "description": "Image"},
                "image/*": {"type": "string", "format": "binary", "example": "image.webp", "description": "Image"},
                "*/*": {"type": "string", "format": "binary", "example": "video.m3u8", "description": "Other"},
            },
        },
    },
)
async def parse(
    data: ParseRequest,
    download: Annotated[
        bool,
        Query(description="If set to `true` and media is single then Returns as stream"),
    ] = False,
) -> GroupedMediaResponse:
    with sentry_sdk.start_transaction(name="Parse", op="parse", description="Parsing") as t:
        with Timer("total_parse_time", transaction=t):
            async with aiohttp.ClientSession() as session:
                media = GroupedMedia.from_medias(
                    await PARSER.parse(
                        session,
                        data.url,
                        use_cache=data.use_cache,
                    )
                )
    if len(media) == 1 and download:
        m = media.flat()[0]
        # noinspection PyTypeChecker
        return StreamingResponse(
            stream_media(m),
            media_type=m.mime_type,
            status_code=status.HTTP_202_ACCEPTED,
            headers={
                # "Content-Disposition": "attachment",
                "X-Original-URL": m.original_url,
            },
        )

    return GroupedMediaResponse(status="ok", result=media)


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
            sentry_status=sentry_settings.feedback_enabled,
        )

    return FeedbackResponse(
        status="ok",
        sentry_status=sentry_settings.feedback_enabled,
    )
