import logging
from typing import Generic, Self, TypeVar

import pymongo
from async_lru import alru_cache
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient as Client
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from pydantic import BaseConfig, BaseModel, Field
from pymongo.errors import CollectionInvalid

from ..settings import mongo_settings as settings

client = Client(settings.url)
db: Database = client[settings.database]

logger = logging.Logger(__name__)


@alru_cache
async def get_collection(name: str) -> Collection:
    try:
        collection = await db.create_collection(name)
    except CollectionInvalid as e:
        if e.args[0] != f"collection {name} already exists":
            raise e
        collection = db.get_collection(name)
    return collection


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


ID = TypeVar("ID", bound=PyObjectId)


class MongoConfig(BaseConfig):
    collection: str | None = None
    allow_population_by_field_name = True
    arbitrary_types_allowed = True
    json_encoders = {ObjectId: str}


class MongoModel(BaseModel, Generic[ID]):
    id: ID = Field(default_factory=PyObjectId, alias="_id")

    class Config(MongoConfig):
        pass

    @classmethod
    async def collection(cls) -> Collection:
        return await get_collection(cls.Config.collection)

    @classmethod
    async def find(cls, object_id: ID | None) -> Self | None:
        if not object_id:
            return None
        try:
            col = await cls.collection()
            res = await col.find_one({"_id": object_id})
        except pymongo.errors.OperationFailure:
            logger.error("Can't find collection %s", object_id, exc_info=True)
            return None
        if res is None:
            return None
        return cls.parse_obj(res)

    async def delete(self):
        try:
            col = await self.collection()
            return await col.delete_one({"_id": self.id})
        except pymongo.errors.OperationFailure:
            logger.error("Can't delete", exc_info=True)
            return None

    async def save(self):
        try:
            col = await self.collection()
            old = await col.find_one({"_id": self.id})
            if old:
                return await col.update_one({"_id": self.id}, {"$set": self.dict(by_alias=True)})
            return await col.insert_one(self.dict(by_alias=True))
        except pymongo.errors.OperationFailure:
            logger.error("Can't save", exc_info=True)
            return None
