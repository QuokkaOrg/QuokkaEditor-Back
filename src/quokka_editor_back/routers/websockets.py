import asyncio
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from quokka_editor_back.routers import manager
from quokka_editor_back.utils.actors import transform_document
from quokka_editor_back.utils.redis import get_redis

router = APIRouter(
    tags=["websockets"],
)


async def forward_from_redis_to_websocket(websocket: WebSocket, document_id: UUID):
    redis_client = await get_redis()
    pubsub = redis_client.pubsub()  # Using async_pubsub()
    await pubsub.psubscribe(f"{str(document_id)}_{id(websocket)}")
    try:
        async for message in pubsub.listen():
            if message and message["type"] in ["message", "pmessage"]:
                await manager.broadcast(
                    message["data"].decode("utf-8"), websocket, document_id
                )
                print(f"{datetime.now()} finish {message['data']}")
    finally:
        await redis_client.close()


@router.websocket("/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: UUID):
    await manager.connect(websocket, document_id)

    listen_task = asyncio.create_task(
        forward_from_redis_to_websocket(websocket, document_id)
    )

    try:
        while True:
            data = await websocket.receive_text()
            print(f"{datetime.now()} start {data}")
            transform_document.send(str(document_id), str(id(websocket)), data)
    except WebSocketDisconnect:
        listen_task.cancel()  # Cancel the Redis listening task
        manager.disconnect(websocket, document_id)
