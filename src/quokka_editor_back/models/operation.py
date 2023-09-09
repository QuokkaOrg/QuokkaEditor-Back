from enum import StrEnum
from tortoise import models, fields


class OperationType(StrEnum):
    INSERT = "INSERT"
    DELETE = "DELETE"


class Operation(models.Model):
    id = fields.UUIDField(pk=True)
    pos = fields.IntField()
    content = fields.CharField(max_length=255, null=True)
    type = fields.CharEnumField(OperationType)
    revision = fields.BigIntField(null=True)  # TODO: remove null=True
