from typing import Self

from media_parser.models import GroupedMedia, Media

from .base import MongoModel


class GroupedMediaModel(GroupedMedia, MongoModel[str]):
    @classmethod
    def from_medias(cls, medias: list[Media]) -> Self:
        self = GroupedMedia.from_medias(medias)

        return cls(
            id=medias[0].original_url,
            audios=self.audios,
            images=self.images,
            videos=self.videos,
        )
