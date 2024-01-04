from pydantic import BaseModel, Field


class DocumentTemplateCreatePayload(BaseModel):
    title: str = Field(..., max_length=255)
    content: list[str]


class DocumentTemplateUpdatePayload(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: list[str] | None = Field(None)
