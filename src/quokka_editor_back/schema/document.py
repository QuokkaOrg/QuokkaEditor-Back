from pydantic import BaseModel, Field

from quokka_editor_back.models.document import ShareRole


class DocumentPayload(BaseModel):
    title: str | None = Field(None, max_length=250)
    content: list[str] | None


class ShareInput(BaseModel):
    shared_role: ShareRole
    shared_by_link: bool
