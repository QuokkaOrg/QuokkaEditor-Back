import random
from collections import defaultdict
from uuid import UUID

from asgiref.sync import sync_to_async
from fastapi import WebSocket

from quokka_editor_back.schema.websocket import MessageTypeEnum


def rand_hex_color():
    r = random.randint(180, 255)
    g = random.randint(180, 255)
    b = random.randint(180, 255)

    hex_color = f"#{r:02X}{g:02X}{b:02X}"
    return hex_color


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[
            UUID, dict[WebSocket, dict[str, str]]
        ] = defaultdict(dict)

    async def send_all_users_info(self, websocket: WebSocket, document_id: UUID):
        all_users = [conn for conn in self.active_connections[document_id].values()]
        await websocket.send_json(all_users)

    async def broadcast_new_user(
        self, username: str, user_token: str, document_id: UUID, websocket: WebSocket
    ):
        websocket_data = {
            "username": username,
            "user_token": user_token,
            "clientColor": rand_hex_color(),
        }
        self.active_connections[document_id][websocket] = websocket_data

        for websocket, data in self.active_connections[document_id].items():
            if data["user_token"] != user_token:
                await websocket.send_json(data)

    async def connect(
        self, websocket: WebSocket, document_id: UUID, username: str, user_token: str
    ):
        await websocket.accept()
        await self.send_all_users_info(websocket, document_id)
        await self.broadcast_new_user(username, user_token, document_id, websocket)

    @sync_to_async()
    def disconnect(self, websocket: WebSocket, document_id: UUID):
        del self.active_connections[document_id][websocket]

    @staticmethod
    async def ack_message(websocket: WebSocket, revision: int, user_token: str):
        await websocket.send_json(
            {
                "revision_log": revision,
                "user_token": user_token,
                "type": MessageTypeEnum.ACKNOWLEDGE,
            }
        )

    async def broadcast(
        self,
        message: dict,
        websocket: WebSocket,
        document_id: UUID,
        user_token: str,
        revision: int | None = None,
        send_to_owner: bool = True,
    ):
        for websocket_conn, data in self.active_connections[document_id].items():
            if user_token == data["user_token"]:
                if send_to_owner:
                    await self.ack_message(websocket, revision, user_token)
            else:
                await websocket_conn.send_json(message)
