import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from starlette import status
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.auth.utils import get_current_user
from quokka_editor_back.models.document import DocumentTemplate
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.document_template import (
    DocumentTemplateCreatePayload,
    DocumentTemplateUpdatePayload,
)

router = APIRouter(tags=["document_templates"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: DocumentTemplateCreatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
):
    new_document = await DocumentTemplate.create(
        title=payload.title,
        content=json.dumps(payload.content).encode(),
    )
    return new_document


@router.get("/", response_model=Page)
async def read_all(current_user: Annotated[User, Depends(get_current_user)]):
    qs = DocumentTemplate.all()
    return await paginate(query=qs.order_by("-id"))


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
    payload: DocumentTemplateUpdatePayload,
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


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
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


add_pagination(router)
