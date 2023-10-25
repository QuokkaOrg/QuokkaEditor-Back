from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, document_id: UUID):
        await websocket.accept()
        self.active_connections[document_id].add(websocket)

    def disconnect(self, websocket: WebSocket, document_id: UUID):
        self.active_connections[document_id].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def ack_message(
        self, websocket: WebSocket, message: str, revision: int, token: str
    ):
        await websocket.send_json(
            {
                "message": message,
                "revision_log": revision,
                "token_id": token,
            }
        )

    async def broadcast(
        self,
        message: str,
        websocket: WebSocket,
        document_id: UUID,
        token: str,
        revision: int | None = None,
        send_to_owner: bool = True,
    ):
        for connection in self.active_connections[document_id]:
            if websocket is connection:
                if send_to_owner:
                    await self.ack_message(websocket, "ACK", revision, token)
            else:
                await connection.send_text(message)
