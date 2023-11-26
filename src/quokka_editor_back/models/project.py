from tortoise import fields, models

from quokka_editor_back.models.document import Document
from quokka_editor_back.models.user import User


class Project(models.Model):
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=250)

    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        model_name="quokka_editor_back.User",
        related_name="projects",
        on_delete=fields.CASCADE,
    )
    documents: fields.ForeignKeyRelation[Document] = fields.ForeignKeyField(
        model_name="quokka_editor_back.Document",
        related_name="projects",
        on_delete=fields.SET_NULL,
        null=True,
    )
    images = fields.TextField(null=True)
