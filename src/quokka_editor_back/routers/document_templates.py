import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.auth.utils import get_current_user
from quokka_editor_back.models.document import DocumentTemplate
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.document import DocumentPayload
from quokka_editor_back.schema.utils import Status

router = APIRouter(tags=["document_templates"])


@router.post("/")
async def create_template(
    payload: DocumentPayload,
    current_user: Annotated[User, Depends(get_current_user)],
):
    new_document = await DocumentTemplate.create(
        title=payload.title,
        content=json.dumps(payload.content).encode(),
    )
    return new_document


@router.get("/")
async def read_all(current_user: Annotated[User, Depends(get_current_user)]):
    return await DocumentTemplate.all()


@router.get("/{template_id}")
async def get_template(
    template_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await DocumentTemplate.get(id=template_id)
    except DoesNotExist as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document Template {template_id} not found",
        ) from err


@router.patch(
    "/{template_id}",
)
async def update_template(
    template_id: UUID,
    payload: DocumentPayload,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        document_template = await DocumentTemplate.get(id=template_id)
    except DoesNotExist as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document Template {template_id} not found",
        ) from err
    if payload.title:
        document_template.title = payload.title
    if payload.content:
        document_template.content = json.dumps(payload.content).encode()

    await document_template.save()
    return document_template


@router.delete("/{template_id}", response_model=Status)
async def delete_template(
    template_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    is_deleted = await DocumentTemplate.filter(id=template_id).delete()
    if not is_deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Document Template{template_id} not found",
        )
    return Status(message=f"Deleted document Template {template_id}")
