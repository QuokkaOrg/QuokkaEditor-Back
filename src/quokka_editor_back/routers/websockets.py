import asyncio
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
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe(f"{str(document_id)}_{id(websocket)}")
    try:
        async for message in pubsub.listen():
            if message and message["type"] in ["message", "pmessage"]:
                await manager.broadcast(
                    message["data"].decode("utf-8"), websocket, document_id
                )
    finally:
        await redis_client.close()


@router.websocket("/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: UUID):
    await manager.connect(websocket, document_id)

    listen_task = asyncio.create_task(
        forward_from_redis_to_websocket(websocket, document_id)
    )
    redis_client = await get_redis()

    try:
        while True:
            data = await websocket.receive_text()
            await redis_client.rpush(f"document_operations_{document_id}", data)

            if not await redis_client.exists(f"document_processing_{document_id}"):
                await redis_client.set(f"document_processing_{document_id}", 1)
                transform_document.send(str(document_id), id(websocket))
    except WebSocketDisconnect:
        listen_task.cancel()
        manager.disconnect(websocket, document_id)
