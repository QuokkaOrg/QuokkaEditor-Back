from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette import status
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import DoesNotExist
from quokka_editor_back.models.operation import Operation, OperationType
from quokka_editor_back.utils.ot import apply_operation, transform

from quokka_editor_back.models.document import Document
from quokka_editor_back.models.user import User
from quokka_editor_back.routers.auth import get_current_user

router = APIRouter(tags=["documents"])


class OperationIn(BaseModel):
    pos: int
    char: str | None = None
    type: OperationType


class OperationOut(OperationIn):
    id: UUID


class DocumentSchema(BaseModel):
    title: str = Field(max_length=250)
    content: str | None


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


@router.get("/", response_model=list[DocumentResponse])
async def read_all():
    return await Document.all().prefetch_related("operations")


@router.post("/", response_model=DocumentResponse)
async def create_document(
    document_payload: DocumentSchema,
    current_user: Annotated[User, Depends(get_current_user)],
):
    new_document = await Document.create(
        title=document_payload.title,
        content=document_payload.content.encode() if document_payload.content else None,
        user=current_user,
    )
    return new_document


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}},
)
async def read_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
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
    document = await get_document(document_id=document_id, user=current_user)
    await document.delete()


async def sync_document_task(document: Document, ops: list[OperationIn]):
    operations = []
    content = (document.content or b"").decode()
    for op_data in ops:
        if op_data.type in (OperationType.INSERT, OperationType.DELETE):
            op = Operation(pos=op_data.pos, char=op_data.char, type=op_data.type)
        else:
            raise HTTPException(status_code=400, detail="Invalid operation type")

        # Transform operation
        for prev_op in operations:
            op = transform(op, prev_op)

        # Apply operation
        content = apply_operation(content, op)

        # Save operation
        operations.append(op)
        await op.save()
        await document.operations.add(op)
        document.update_from_dict({"content": content.encode()})
        await document.save()


@router.post("/{document_id}/edit/")
async def edit_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    ops: list[OperationIn],
):
    document = await get_document(document_id=document_id)
