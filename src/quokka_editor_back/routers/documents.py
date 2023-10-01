from copy import copy
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from pydantic import BaseModel, Field
from starlette import status
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.models.document import Document
from quokka_editor_back.models.operation import Operation, OperationType
from quokka_editor_back.models.user import User
from quokka_editor_back.routers.auth import get_current_user
from quokka_editor_back.utils.ot import apply_operation, transform
from quokka_editor_back.routers.connection_manager import ConnectionManager
from quokka_editor_back.utils.time_execution import timed_execution

router = APIRouter(tags=["documents"])


class OperationIn(BaseModel):
    pos: int
    char: str | None = None
    type: OperationType
    revision: int = Field(..., gte=0)


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
    document = await get_document(document_id=document_id)
    await document.delete()


async def sync_document_task(
    document: Document,
    op_in: OperationIn,
    websocket: WebSocket,
    manager: ConnectionManager,
):
    with timed_execution():
        content = (document.content or b"").decode()
        print(op_in)
        if op_in.type in (OperationType.INSERT, OperationType.DELETE):
            op = Operation(
                pos=op_in.pos,
                content=op_in.char,
                type=op_in.type,
                revision=op_in.revision,
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
        # document.recent_revision = last_op
        op.revision = 0
        await op.save()
        await document.operations.add(op)
        document.update_from_dict({"content": content.encode()})
        await document.save()
        await manager.ack_message(websocket, "ACK", 1)
        await manager.broadcast(op_in.json(), websocket)


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}},
)
async def update_document(
    document_id: UUID,
    document_payload: DocumentSchema,
    # current_user: Annotated[User, Depends(get_current_user)],
):
    document = await get_document(document_id=document_id)
    document.update_from_dict(
        {
            "title": document_payload.title,
            "content": document_payload.content.encode()
            if document_payload.content
            else None,
        }
    )
    await document.save()
    return document
