from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(self.active_connections)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def ack_message(self, websocket: WebSocket, message: str, revision: int):
        await websocket.send_json({"message": message, "revision_log": revision})

    async def broadcast(self, message: str):
        print(self.active_connections)
        for connection in self.active_connections:
            await connection.send_text(message)
