import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.auth.utils import get_current_user
from quokka_editor_back.models.document import Document
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.document import DocumentPayload, ShareInput
from quokka_editor_back.schema.utils import Status

router = APIRouter(tags=["documents"])


async def get_document(document_id: UUID, user: User | None = None) -> Document:
    filters: dict[str, Any] = {"id": document_id}
    if user:
        filters["user"] = user
    try:
        document = await Document.get(**filters)
        return document
    except DoesNotExist as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        ) from err


@router.get("/")
async def read_all(current_user: Annotated[User, Depends(get_current_user)]):
    return await Document.all()


@router.post("/")
async def create_document(
    current_user: Annotated[User, Depends(get_current_user)],
):
    new_document = await Document.create(
        title="Draft Document",
        user_id=current_user.id,
        content=json.dumps([""]).encode(),
    )
    return new_document


@router.get(
    "/{document_id}",
)
async def read_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    document = await get_document(document_id=document_id, user=current_user)
    return document


@router.delete("/{document_id}", response_model=Status)
async def delete_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    is_deleted = await Document.filter(id=document_id, user=current_user).delete()
    if not is_deleted:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    return Status(message=f"Deleted document {document_id}")


@router.patch(
    "/{document_id}",
)
async def update_document(
    document_id: UUID,
    document_payload: DocumentPayload,
    current_user: Annotated[User, Depends(get_current_user)],
):
    document = await get_document(document_id=document_id)
    document.update_from_dict(
        {
            "title": document_payload.title,
            "content": json.dumps(document_payload.content).encode()
            if document_payload.content
            else None,
        }
    )
    await document.save()
    return document


@router.post("/share/{document_id}")
async def share_document(
    document_id: UUID,
    payload: ShareInput,
    current_user: Annotated[User, Depends(get_current_user)],
):
    document = await get_document(document_id=document_id)
    document.update_from_dict(payload.dict())
    await document.save()
    return Status(message=f"Shared document {document_id}")
