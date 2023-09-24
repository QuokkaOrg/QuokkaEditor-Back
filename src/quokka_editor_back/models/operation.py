from enum import StrEnum

from tortoise import fields, models


class OperationType(StrEnum):
    INSERT = "INSERT"
    DELETE = "DELETE"


class RevisionLog(models.Model):
    id = fields.BigIntField(pk=True)
    position = fields.BigIntField
    operationType = fields.CharEnumField(OperationType)


class Operation(models.Model):
    id = fields.UUIDField(pk=True)
    pos = fields.IntField()
    content = fields.CharField(max_length=255, null=True)
    type = fields.CharEnumField(OperationType)
    revision = fields.BigIntField()
