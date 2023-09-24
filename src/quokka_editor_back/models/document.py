from tortoise import fields, models

from quokka_editor_back.models.operation import Operation, RevisionLog
from quokka_editor_back.models.user import User


class Document(models.Model):
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=250)
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
    )
    recent_revision: fields.ForeignKeyRelation[RevisionLog] = fields.ForeignKeyField(
        "quokka_editor_back.RevisionLog"
    )
