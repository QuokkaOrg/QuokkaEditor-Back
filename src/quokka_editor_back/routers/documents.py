from typing import Annotated, Any
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException

from starlette import status
from tortoise.exceptions import DoesNotExist
from quokka_editor_back.auth.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
)

from quokka_editor_back.models.document import Document
from quokka_editor_back.models.user import User


router = APIRouter(tags=["documents"])


async def get_document(document_id: UUID, user: User | None = None) -> Document:
    filters: dict[str, Any] = {"id": document_id}
    if user:
        filters["user"] = user
    try:
        document = await Document.get(**filters)
        return document
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )


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
    )
    return new_document


@router.get(
    "/{document_id}",
)
async def read_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_document(document_id=document_id, user=current_user)


@router.get("/shared/{token}/")
async def read_shared_document(token):
    decoded_token = decode_access_token(token)
    document = await get_document(document_id=uuid.UUID(decoded_token["document_id"]))
    return {"document": document, "permissions": decoded_token["permissions"]}


@router.delete(
    "/{document_id}",
)
async def delete_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    document = await get_document(document_id=document_id, user=current_user)
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


@router.post("/share/{document_id}")
async def share_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    await get_document(document_id=document_id, user=current_user)

    token = create_access_token(
        data={"document_id": str(document_id), "permissions": "edit"}
    )

    return {"token": token}
