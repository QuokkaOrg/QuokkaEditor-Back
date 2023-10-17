import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette import status
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.models.document import Document
from quokka_editor_back.models.operation import OperationType
from quokka_editor_back.models.user import User

from quokka_editor_back.routers.auth import get_current_user

router = APIRouter(tags=["documents"])


class OperationIn(BaseModel):
    pos: int
    content: str | None = None
    type: OperationType
    revision: int = Field(..., gte=0)


class OperationOut(OperationIn):
    id: UUID


class DocumentSchema(BaseModel):
    title: str = Field(max_length=250)
    content: list[str] | None


class DocumentResponse(DocumentSchema):
    id: UUID


async def get_document(document_id: UUID) -> Document:
    try:
        document = await Document.get(id=document_id)
        await document.fetch_related("operations")
        return document
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )


@router.get("/")  # TODO: add response_model
async def read_all():
    return (
        await Document.all()
    )  # TODO: add pydantic model as a serializer and reduce response objects to


@router.post("/")  # TODO: add response_model
async def create_document(
    document_payload: DocumentSchema,
    current_user: Annotated[User, Depends(get_current_user)],
):
    new_document = await Document.create(
        title=document_payload.title,
        content=json.dumps(document_payload.content).encode()
        if document_payload.content
        else None,  # TODO: remove None
        user_id=current_user.id,
    )
    return new_document


@router.get(
    "/{document_id}",
    # response_model=DocumentResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}},
)
async def read_document(
    document_id: UUID,
    # current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_document(document_id=document_id)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}},
)
async def delete_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    document = await get_document(document_id=document_id)
    await document.delete()


# TODO: update this endpoint to use new document content
# @router.patch(
#     "/{document_id}",
#     response_model=DocumentResponse,
#     responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}},
# )
# async def update_document(
#     document_id: UUID,
#     document_payload: DocumentSchema,
#     current_user: Annotated[User, Depends(get_current_user)],
# ):
#     document = await get_document(document_id=document_id)
#     document.update_from_dict(
#         {
#             "title": document_payload.title,
#             "content": document_payload.content.encode()
#             if document_payload.content
#             else None,
#         }
#     )
#     await document.save()
#     return document
