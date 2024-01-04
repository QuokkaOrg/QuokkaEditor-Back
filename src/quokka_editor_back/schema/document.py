from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCreatePayload(BaseModel):
    template_id: UUID | None = None
    project_id: UUID


class DocumentUpdatePayload(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: list[str] | None = Field(None)
