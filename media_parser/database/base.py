import logging
from typing import Any, Self

import pymongo.errors
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler
from pydantic_core import core_schema as cs
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

logger = logging.Logger(__name__)


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
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> cs.CoreSchema:
        return cs.str_schema()


class MongoModel[ID: PyObjectId](BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: ID = Field(default_factory=PyObjectId, alias="_id")

    @classmethod
    def controller(cls, collection: AsyncIOMotorCollection) -> "MongoModelController[ID, Self]":
        return MongoModelController(collection, cls)


class MongoModelController[ID, Model]:
    def __init__(self, collection: AsyncIOMotorCollection, model: type[Model]):
        self.collection = collection
        self.model = model

    async def find(self, object_id: ID | None) -> Model | None:
        """Find method to retrieve an object by its ID.

        :param object_id: The ID of the object to find.
        :return: The found object if it exists, None otherwise.
        """
        if not object_id:
            return None
        try:
            return self.model.model_validate(await self.collection.find_one({"_id": object_id}))
        except pymongo.errors.OperationFailure as exc:
            logger.error("Can't find collection %s", object_id, exc_info=exc)
        return None

    async def delete(self, obj: Model) -> DeleteResult | None:
        """Delete method deletes a document from the collection.

        :returns: If the deletion is successful, returns a DeleteResult object representing the deletion operation.
        If an error occurs during the deletion operation, logs the error and returns None.
        """
        try:
            return await self.collection.delete_one({"_id": obj.id})
        except pymongo.errors.OperationFailure as exc:
            logger.error("Can't delete", exc_info=exc)
        return None

    async def save(self, obj: Model) -> UpdateResult | InsertOneResult | None:
        """Save the current document instance to the collection.

        :returns: Update or InsertOne result.
        None if it can't be saved.
        """
        try:
            old = await self.collection.find_one({"_id": obj.id})
            if old:
                return await self.collection.update_one(
                    {"_id": obj.id},
                    {"$set": obj.model_dump(by_alias=True)},
                )
            return await self.collection.insert_one(obj.model_dump(by_alias=True))
        except pymongo.errors.OperationFailure as exc:
            logger.error("Can't save", exc_info=exc)
        return None
