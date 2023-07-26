from enum import Enum
from typing import Self

from pydantic import BaseModel, Field


class ParserType(str, Enum):
    """BaseParser type."""

    TIKTOK = "TikTok"
    TWITTER = "Twitter"
    YOUTUBE = "YouTube"
    REDDIT = "Reddit"
    INSTAGRAM = "Instagram"


class Media(BaseModel):
    caption: str
    type: ParserType
    original_url: str
    caption: str | None = None
    thumbnail_url: str | None = None
    author: str | None = None
    extra_description: str = ""
    language: str | None = None
    mime_type: str | None = None

    def __hash__(self):
        return hash(self.original_url)


class Video(Media):
    url: str = ""
    max_quality_url: str | None = None
    audio_url: str | None = None  # Is it necessary?
    mime_type: str = "video/mp4"

    height: int | None = None
    width: int | None = None
    duration: int | None = None

    def __bool__(self):
        return bool(self.url)


class Image(Media):
    url: str
    max_quality_url: str | None = None
    mime_type: str = "image/jpeg"
    height: int | None = None
    width: int | None = None

    def __bool__(self):
        return bool(self.url)


class Audio(Media):
    url: str = ""
    mime_type: str = "audio/mpeg"


class GroupedMedia(BaseModel):
    audios: list[Audio] = Field(default_factory=list)
    images: list[Image] = Field(default_factory=list)
    videos: list[Video] = Field(default_factory=list)

    @classmethod
    def from_medias(cls, medias: list[Media]) -> Self:
        return cls(
            audios=[m for m in medias if isinstance(m, Audio)],
            images=[m for m in medias if isinstance(m, Image)],
            videos=[m for m in medias if isinstance(m, Video)],
        )

    def __bool__(self):
        return bool(self.audios or self.images or self.videos)

    def flat(self) -> list[Media]:
        return self.audios + self.images + self.videos

    def __len__(self):
        return len(self.audios + self.images + self.videos)

    def __add__(self, other: Self):
        return GroupedMedia(
            audios=self.audios + other.audios,
            images=self.images + other.images,
            videos=self.videos + other.videos,
        )
