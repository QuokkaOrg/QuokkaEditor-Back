import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from starlette import status
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from quokka_editor_back.auth.utils import get_current_user
from quokka_editor_back.models.document import Document, DocumentTemplate
from quokka_editor_back.models.project import Project
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.document import (
    DocumentCreatePayload,
    DocumentUpdatePayload,
)

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


@router.get("/", response_model=Page)
async def read_all(
    current_user: Annotated[User, Depends(get_current_user)],
    search_phrase: str | None = Query(None),
):
    qs = Document.filter(user=current_user)
    if search_phrase:
        qs = qs.filter(Q(title__icontains=search_phrase))

    return await paginate(query=qs.order_by("-id"))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_document(
    current_user: Annotated[User, Depends(get_current_user)],
    document_payload: DocumentCreatePayload,
):
    title = "Draft Document"
    content = json.dumps([""]).encode()

    if document_payload.template_id:
        try:
            document_template = await DocumentTemplate.get(
                id=document_payload.template_id
            )
        except DoesNotExist as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document Template {document_payload.template_id} not found",
            ) from err
        title = document_template.title
        content = document_template.content

    try:
        project = await Project.get(id=document_payload.project_id)
    except DoesNotExist as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {document_payload.project_id} not found",
        ) from err

    new_document = await Document.create(
        title=title,
        user_id=current_user.id,
        content=content,
        project=project,
    )
    return new_document


@router.get("/{document_id}")
async def read_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_document(document_id=document_id, user=current_user)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    is_deleted = await Document.filter(id=document_id, user=current_user).delete()
    if not is_deleted:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")


@router.patch(
    "/{document_id}",
)
async def update_document(
    document_id: UUID,
    document_payload: DocumentUpdatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
):
    document = await get_document(document_id=document_id)
    if document_payload.title:
        document.title = document_payload.title
    if document_payload.content:
        document.content = json.dumps(document_payload.content).encode()
    await document.save()
    return document


add_pagination(router)
