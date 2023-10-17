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

    async def ack_message(self, websocket: WebSocket, message: str, revision: int):
        await websocket.send_json({"message": message, "revision_log": revision})

    async def broadcast(self, message: str, websocket: WebSocket, document_id: UUID):
        for connection in self.active_connections[document_id]:
            if websocket is connection:
                await self.ack_message(websocket, "ACK", 0)
            else:
                await connection.send_text(message)
