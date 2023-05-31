from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from quokka_editor_back.routers.connection_manager import ConnectionManager


router = APIRouter(
    tags=["websockets"],
)

manager = ConnectionManager()


@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
