from fastapi import File, UploadFile
from pydantic import BaseModel, Field


class ProjectUpdatePayload(BaseModel):
    title: str | None = Field(None, max_length=255)


class ProjectImagePayload(BaseModel):
    file: UploadFile = File(...)
