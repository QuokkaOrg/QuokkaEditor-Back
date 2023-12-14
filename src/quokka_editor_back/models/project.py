from enum import StrEnum

from tortoise import fields, models

from quokka_editor_back.models.user import User


class ShareRole(StrEnum):
    READ = "READ"
    COMMENT = "COMMENT"
    EDIT = "EDIT"


class Project(models.Model):
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=255)

    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        model_name="quokka_editor_back.User",
        related_name="projects",
        on_delete=fields.CASCADE,
    )
    images = fields.JSONField(null=True)
    shared_role = fields.CharEnumField(ShareRole, default=ShareRole.READ)
    shared_by_link = fields.BooleanField(default=False)
