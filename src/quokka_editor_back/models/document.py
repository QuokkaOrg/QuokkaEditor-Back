from enum import StrEnum

from tortoise import fields, models

from quokka_editor_back.models.operation import Operation
from quokka_editor_back.models.user import User


class ShareRole(StrEnum):
    READ = "READ"
    COMMENT = "COMMENT"
    EDIT = "EDIT"


class Document(models.Model):
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=252)
    content = fields.BinaryField(null=True)

    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        model_name="quokka_editor_back.User",
        related_name="documents",
        on_delete=fields.CASCADE,
    )
    operations: fields.ManyToManyRelation[Operation] = fields.ManyToManyField(
        model_name="quokka_editor_back.Operation",
        related_name="operations",
        on_delete=fields.SET_NULL,
        through="document_operation",
        null=True,
    )
    last_revision = fields.BigIntField(default=0)
    shared_role = fields.CharEnumField(ShareRole, default=ShareRole.READ)
    shared_by_link = fields.BooleanField(default=False)


class DocumentTemplate(models.Model):
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=250)
    content = fields.BinaryField(null=True)
