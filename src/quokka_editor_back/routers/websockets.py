import asyncio
import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from quokka_editor_back.auth.auth import get_current_user
from quokka_editor_back.models.user import User

from quokka_editor_back.routers import manager
from quokka_editor_back.actors import transform_document
from quokka_editor_back.routers.documents import get_document
from quokka_editor_back.utils.redis import get_redis

logger = logging.getLogger(__name__)
router = APIRouter(
    tags=["websockets"],
)


async def forward_from_redis_to_websocket(
    websocket: WebSocket, document_id: UUID, token: str
):
    redis_client = await get_redis()
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe(f"{str(document_id)}_{token}")
    try:
        async for message in pubsub.listen():
            if message and message["type"] in ["message", "pmessage"]:
                logger.debug("Broadcast message %s", message["data"])
                loaded_message = json.loads(message["data"].decode("utf-8"))
                await manager.broadcast(
                    message=loaded_message["data"],
                    websocket=websocket,
                    document_id=document_id,
                    revision=loaded_message["revision"],
                    token=token,
                )
    finally:
        await pubsub.unsubscribe(f"{str(document_id)}_{token}")
        await redis_client.close()


@router.websocket("/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: UUID, token: str):
    await manager.connect(websocket, document_id)

    listen_task = asyncio.create_task(
        forward_from_redis_to_websocket(websocket, document_id, token)
    )
    redis_client = await get_redis()

    try:
        while True:
            data = (
                await websocket.receive_text()
            )  # TODO: add validation here with OperationSchema
            json_data = json.loads(data)
            new_data = {"data": data, "token_id": token}
            if json_data["type"] == "cursor":
                await manager.broadcast(
                    data, websocket, document_id=document_id, send_to_owner=False, token=token
                )
                continue
            logger.debug("Input data %s", data)
            await redis_client.rpush(
                f"document_operations_{document_id}", json.dumps(new_data)
            )

            if not await redis_client.exists(f"document_processing_{document_id}"):
                await redis_client.set(f"document_processing_{document_id}", 1)
                transform_document.send(str(document_id))
    except WebSocketDisconnect:
        listen_task.cancel()
    finally:
        manager.disconnect(websocket, document_id)
        await redis_client.close()
