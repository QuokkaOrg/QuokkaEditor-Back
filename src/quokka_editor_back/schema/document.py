from uuid import UUID

from pydantic import BaseModel, Field

from quokka_editor_back.models.document import ShareRole


class DocumentCreatePayload(BaseModel):
    template_id: UUID | None = None
    project_id: UUID


class DocumentUpdatePayload(BaseModel):
    title: str | None = Field(None, max_length=250)
    content: list[str] | None = Field(None)


class ShareInput(BaseModel):
    shared_role: ShareRole
    shared_by_link: bool
