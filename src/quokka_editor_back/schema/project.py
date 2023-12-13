from fastapi import File, UploadFile
from pydantic import BaseModel, Field


class ProjectCreatePayload(BaseModel):
    title: str = Field(max_length=255)


class ProjectUpdatePayload(BaseModel):
    title: str | None = Field(None, max_length=255)


class ProjectImagePayload(BaseModel):
    file: UploadFile = File(...)
