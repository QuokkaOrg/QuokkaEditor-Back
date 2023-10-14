from enum import StrEnum

from pydantic import BaseModel, Field
from tortoise import fields, models


class OperationType(StrEnum):
    INPUT = "+INPUT"
    DELETE = "+DELETE"
    PASTE = "PASTE"
    UNDO = "UNDO"

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda item: item.value, cls))


class PosSchema(BaseModel):
    line: int
    ch: int


class OperationSchema(BaseModel):
    from_pos: PosSchema
    to_pos: PosSchema
    text: list[str]
    type: OperationType
    revision: int = Field(..., gte=0)


class Operation(models.Model):
    id = fields.UUIDField(pk=True)
    from_pos = fields.TextField()
    to_pos = fields.TextField()
    text = fields.TextField()
    type = fields.CharEnumField(OperationType)
    revision = fields.BigIntField()
