from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field

__all__ = (
    "ParserType",
    "Media",
    "Video",
    "Image",
    "Audio",
    "GroupedMedia",
)


class ParserType(StrEnum):
    """
    BaseParser types. Using for identify parsers.
    """

    TIKTOK = "TikTok"
    TWITTER = "Twitter"
    YOUTUBE = "YouTube"
    REDDIT = "Reddit"
    INSTAGRAM = "Instagram"
    VK = "VK"


class Media(BaseModel):
    """
    Base class for all medias.

    :param type: Type source of media (TikTok, Twitter, YouTube, Reddit, Instagram)
    :param original_url: Original URL of media
    :param url: URL to media content
    :param caption: Caption of media
    :param thumbnail_url: URL to thumbnail
    :param author: Author of media
    :param extra_description: Extra description
    :example extra_description: `"Video from YouTube"`
    :param language: Language of media
    :example language: `"en"`
    :param mime_type: MIME type of media
    :example mime_type: `"video/mp4"`
    """

    type: ParserType
    original_url: str
    url: str = ""
    caption: str | None = None
    thumbnail_url: str | None = None
    author: str | None = None
    extra_description: str = ""
    language: str | None = None
    mime_type: str | None = None

    headers: dict[str, str] = Field(default_factory=dict, exclude=True)

    def __hash__(self):
        return hash(self.original_url)


class Video(Media):
    """
    Video media.

    :param max_quality_url: URL to max quality video.
    :info max_quality_url: If max quality video is not available, max_quality_url is equal to url.
    :param audio_url: URL to audio from video.
    :info audio_url: Is it necessary?
    :param height: Height of video.
    :param width: Width of video.
    :param duration: Duration of video.
    """

    max_quality_url: str | None = None
    audio_url: str | None = None  # Is it necessary?
    mime_type: str = "video/mp4"

    height: int | None = None
    width: int | None = None
    duration: int | None = None

    def __bool__(self):
        return bool(self.url)


class Image(Media):
    """
    Image media.

    :param max_quality_url: URL to max quality image.
    :info max_quality_url: If max quality image is not available, max_quality_url is equal to url.
    :param height: Height of image.
    :param width: Width of image.
    """

    max_quality_url: str | None = None
    mime_type: str = "image/jpeg"
    height: int | None = None
    width: int | None = None

    def __bool__(self) -> bool:
        """
        Return True if Image has url.
        """
        return bool(self.url)


class Audio(Media):
    """
    Audio media.

    :param mime_type: MIME type of audio.
    """

    mime_type: str = "audio/mpeg"

    def __bool__(self) -> bool:
        """
        Return True if Audio has url.
        """
        return bool(self.url)


class GroupedMedia(BaseModel):
    audios: list[Audio] = Field(default_factory=list)
    images: list[Image] = Field(default_factory=list)
    videos: list[Video] = Field(default_factory=list)

    @classmethod
    def from_medias(cls, medias: list[Media]) -> Self:
        """
        Generate GroupedMedia from a list of Media.

        :param medias: List of Media.
        :return: Grouped Media.
        """

        return cls(
            audios=[m for m in medias if isinstance(m, Audio)],
            images=[m for m in medias if isinstance(m, Image)],
            videos=[m for m in medias if isinstance(m, Video)],
        )

    def __bool__(self) -> bool:
        """
        Return True if GroupedMedia has any medias.
        """

        return bool(self.audios or self.images or self.videos)

    def flat(self) -> list[Media]:
        """
        Makes a list of Media from GroupedMedia.
        """

        return self.audios + self.images + self.videos

    def __len__(self) -> int:
        """
        Return count of all medias.
        """
        return len(self.audios) + len(self.images) + len(self.videos)

    def __add__(self, other: Self) -> Self:
        """
        Concatenate two GroupedMedia.

        :param other: GroupedMedia.
        :return: GroupedMedia.
        """

        return GroupedMedia(
            audios=self.audios + other.audios,
            images=self.images + other.images,
            videos=self.videos + other.videos,
        )

    @classmethod
    def merge(cls, *grouped_medias: Self) -> Self:
        return GroupedMedia(
            audios=[audio for groups in grouped_medias for audio in groups.audios],
            images=[image for groups in grouped_medias for image in groups.images],
            videos=[video for groups in grouped_medias for video in groups.videos],
        )


class GroupedMediaResult(GroupedMedia):
    event_id: str | None = None
    request_url: str | None = None
