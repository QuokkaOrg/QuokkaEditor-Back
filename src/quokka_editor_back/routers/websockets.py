import asyncio
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect

from quokka_editor_back.routers.connection_manager import ConnectionManager
from quokka_editor_back.routers.documents import (
    OperationIn,
    get_document,
    sync_document_task,
)
from quokka_editor_back.utils.time_execution import timed_execution

router = APIRouter(
    tags=["websockets"],
)

manager = ConnectionManager()


@router.websocket("/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: UUID):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            document = await get_document(document_id=document_id)
            op = OperationIn.parse_raw(data)
            asyncio.ensure_future(sync_document_task(document, op, websocket, manager))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
