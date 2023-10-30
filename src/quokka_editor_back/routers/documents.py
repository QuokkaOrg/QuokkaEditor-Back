import contextlib
import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from starlette import status
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.auth import security
from quokka_editor_back.auth.utils import get_current_user
from quokka_editor_back.models.document import Document, DocumentTemplate
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.document import DocumentPayload, ShareInput
from quokka_editor_back.schema.utils import Status

router = APIRouter(tags=["documents"])


async def get_document(
    document_id: UUID,
    user: User | None = None,
) -> Document:
    filters: dict[str, Any] = {"id": document_id}
    if user:
        filters["user"] = user
    try:
        document = await Document.get(**filters).prefetch_related("user")
        return document
    except DoesNotExist as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        ) from err


@router.get("/")
async def read_all(current_user: Annotated[User, Depends(get_current_user)]):
    return await Document.filter(user=current_user)


@router.post("/")
async def create_document(
    current_user: Annotated[User, Depends(get_current_user)],
    template_id: UUID | None = None,
):
    title = "Draft Document"
    content = json.dumps([""]).encode()

    if template_id:
        try:
            document_template = await DocumentTemplate.get(id=template_id)
        except DoesNotExist as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document Template {template_id} not found",
            ) from err
        title = document_template.title
        content = document_template.content

    new_document = await Document.create(
        title=title,
        user_id=current_user.id,
        content=content,
    )
    return new_document


def has_access(document: Document, current_user: User | None):
    if document.shared_by_link:
        return True
    if current_user and document.user == current_user:
        return True
    return False


@router.get("/{document_id}")
async def read_document(
    document_id: UUID,
    credentials: HTTPAuthorizationCredentials | None = Security(security),
):
    document = await get_document(document_id=document_id)
    current_user = None

    if credentials:
        with contextlib.suppress(HTTPException):
            current_user = await get_current_user(credentials)

    if not has_access(document, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

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
    if document_payload.title:
        document.title = document_payload.title
    if document_payload.content:
        document.content = json.dumps(document_payload.content).encode()
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
