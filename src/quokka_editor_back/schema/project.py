from fastapi import File, UploadFile
from pydantic import BaseModel, Field

from quokka_editor_back.models.project import ShareRole


class ProjectCreatePayload(BaseModel):
    title: str = Field(max_length=255)


class ProjectUpdatePayload(BaseModel):
    title: str | None = Field(None, max_length=255)


class ProjectImagePayload(BaseModel):
    file: UploadFile = File(...)


class ShareInput(BaseModel):
    shared_role: ShareRole
    shared_by_link: bool
