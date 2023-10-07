from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from quokka_editor_back.routers import manager

from quokka_editor_back.utils.actors import transform_document


router = APIRouter(
    tags=["websockets"],
)


@router.websocket("/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: UUID):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            transform_document.send(str(document_id), data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
