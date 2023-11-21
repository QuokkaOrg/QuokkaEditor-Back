import json
import random
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


def rand_hex_color():
    chars = "0123456789ABCDEF"
    hex_color = "#"
    for _ in range(6):
        hex_color += random.choice(chars)
    return hex_color


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[
            UUID, dict[WebSocket, dict[str, str]]
        ] = defaultdict(dict)

    async def connect(
        self, websocket: WebSocket, document_id: UUID, username: str, user_token: str
    ):
        await websocket.accept()

        all_users = [conn for conn in self.active_connections[document_id].values()]
        await websocket.send_text(json.dumps(all_users))

        websocket_data = {
            "username": username,
            "user_token": user_token,
            "ch": 0,
            "line": 0,
            "clientColor": rand_hex_color(),
        }
        self.active_connections[document_id][websocket] = websocket_data

        await self.broadcast_user_connected(document_id, user_token)

    async def broadcast_user_connected(self, document_id: UUID, user_token: str):
        for websocket, data in self.active_connections[document_id].items():
            if data["user_token"] != user_token:
                await websocket.send_text(json.dumps(data))

    def disconnect(self, websocket: WebSocket, document_id: UUID):
        del self.active_connections[document_id][websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def ack_message(
        self, websocket: WebSocket, message: str, revision: int, user_token: str
    ):
        await websocket.send_json(
            {
                "message": message,
                "revision_log": revision,
                "user_token": user_token,
            }
        )

    async def broadcast(
        self,
        message: str,
        websocket: WebSocket,
        document_id: UUID,
        user_token: str,
        revision: int | None = None,
        send_to_owner: bool = True,
    ):
        for websocket_conn, data in self.active_connections[document_id].items():
            if user_token == data["user_token"]:
                if send_to_owner:
                    await self.ack_message(websocket, "ACK", revision, user_token)
            else:
                await websocket_conn.send_text(message)
