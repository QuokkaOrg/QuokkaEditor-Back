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
from fastapi import BackgroundTasks

router = APIRouter(tags=["documents"])


class OperationIn(BaseModel):
    pos: int
    char: str | None = None
    type: OperationType
    revision: int = Field(..., gte=0)


PENDING_CHANGES: list[OperationIn] = [
    OperationIn(pos=0, char="Hello", type=OperationType.INSERT, revision=0),
    OperationIn(pos=5, char=" World", type=OperationType.INSERT, revision=1),
    OperationIn(pos=11, char="!", type=OperationType.INSERT, revision=1),
]


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
    document = await get_document(document_id=document_id, user=current_user)
    await document.delete()


async def sync_document_task(document: Document):
    operations = []
    content = (document.content or b"").decode()
    for op in PENDING_CHANGES:
        # TODO: do this in transaction
        if op.type in (OperationType.INSERT, OperationType.DELETE):
            op = Operation(
                pos=op.pos, content=op.char, type=op.type, revision=op.revision
            )
        else:
            # TODO: USE LOGGER AND DO NOT RAISE EXC
            raise HTTPException(status_code=400, detail="Invalid operation type")

        # Transform operation
        last_op = await document.operations.order_by("-revision").first()
        if last_op and op.revision <= last_op.revision:
            op.revision = last_op.revision + 1
            for prev_op in await document.operations.filter(revision__gte=op.revision):
                op = transform(op, prev_op)

        # Apply operation
        content = apply_operation(content, op)

        # Save operation
        operations.append(op)
        await op.save()
        await document.operations.add(op)
        document.update_from_dict({"content": content.encode()})
        await document.save()
        # TODO: websocket broadcast (ack, op_type) with revision


@router.post("/{document_id}/edit/")
async def edit_document(
    document_id: UUID,
    # current_user: Annotated[User, Depends(get_current_user)],
    # op: list[OperationIn],
    background_tasks: BackgroundTasks,
):
    document = await get_document(document_id=document_id)
    # PENDING_CHANGES.append(op[0])
    background_tasks.add_task(sync_document_task, document)
