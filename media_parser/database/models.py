from typing import Self

from pydantic import Field

from models import GroupedMedia, Media

from .base import MongoModel


class GroupedMediaModel(GroupedMedia, MongoModel[str]):
    id: str = Field(..., alias="_id", description="Origin URL of media")

    class Config(MongoModel.Config):
        collection = "medias"

    @classmethod
    def from_medias(cls, medias: list[Media]) -> Self:
        self = GroupedMedia.from_medias(medias)

        return cls(
            id=medias[0].original_url,
            audios=self.audios,
            images=self.images,
            videos=self.videos,
        )
