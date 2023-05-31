from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException
from starlette import status
from quokka_editor_back.models.document import Document
from tortoise.exceptions import DoesNotExist
from uuid import UUID

router = APIRouter(tags=["documents"])


class DocumentPayload(BaseModel):
    title: str = Field("", max_length=250)
    content: str = Field("")


class DocumentResponse(DocumentPayload):
    id: UUID


@router.get("/")
async def read_all():
    return await Document.all()


@router.get("/{document_id}")
async def read_document(document_id: UUID):
    try:
        return await Document.get(id=document_id)
    except DoesNotExist:
        raise http_exception()


@router.post("/", response_model=DocumentResponse)
async def create_document(document_payload: DocumentPayload):
    new_document = await Document.create(
        title=document_payload.title, content=document_payload.content.encode()
    )
    return DocumentResponse.parse_obj(new_document)


@router.patch("/{document_id}")
async def update_document(document_id: UUID, document_payload: DocumentPayload):
    try:
        document = await Document.get(id=document_id)
    except DoesNotExist:
        raise http_exception()
    document.title = document_payload.title
    document.content = document_payload.content.encode()
    return DocumentResponse.parse_obj(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID):
    try:
        document = await Document.get(id=document_id)
    except DoesNotExist:
        raise http_exception()
    await document.delete()


def http_exception():
    return HTTPException(status_code=404, detail="Document not found")
