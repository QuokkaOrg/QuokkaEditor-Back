import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis as AsyncRedis
from redis.client import PubSub

from quokka_editor_back.actors import transform_document
from quokka_editor_back.auth.utils import authenticate_websocket
from quokka_editor_back.models.project import ShareRole
from quokka_editor_back.routers import manager
from quokka_editor_back.utils.redis import get_redis

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websockets"])


def decode_redis_message(message: dict) -> dict:
    return json.loads(message["data"].decode("utf-8"))


# TODO add test for subscribe_channel_and_broadcast_redis_messages
async def subscribe_channel_and_broadcast_redis_messages(
    pubsub: PubSub,
    websocket: WebSocket,
    document_id: UUID,
    user_token: str,
    channel_name: str,
):
    await pubsub.psubscribe(channel_name)

    try:
        async for message in pubsub.listen():
            if message and message["type"] in ["message", "pmessage"]:
                logger.debug("Broadcast message %s", message["data"])
                decoded_message = decode_redis_message(message)
                await manager.broadcast(
                    message=decoded_message,
                    websocket=websocket,
                    document_id=document_id,
                    revision=decoded_message["revision"],
                    user_token=user_token,
                )
    finally:
        await pubsub.unsubscribe(channel_name)


async def forward_from_redis_to_websocket(
    websocket: WebSocket, document_id: UUID, user_token: str
):
    redis_client = await get_redis()
    channel_name = f"{str(document_id)}_{user_token}"

    pubsub = redis_client.pubsub()
    await subscribe_channel_and_broadcast_redis_messages(
        pubsub, websocket, document_id, user_token, channel_name
    )

    await redis_client.close()


async def process_websocket_message(
    data: str,
    websocket: WebSocket,
    redis_client: AsyncRedis,
    document_id: UUID,
    user_token: str,
    read_only: bool,
):
    json_data = json.loads(data)
    new_data = {"data": json_data, "user_token": user_token}

    if json_data["type"] == "cursor":
        await manager.broadcast(
            new_data,
            websocket,
            document_id=document_id,
            send_to_owner=False,
            user_token=user_token,
        )
        return

    logger.debug("Input data %s", new_data)

    if read_only:
        return
    await redis_client.rpush(f"document_operations_{document_id}", json.dumps(new_data))
    if await redis_client.set(f"document_processing_{document_id}", 1, nx=True):
        transform_document.send(str(document_id))


@router.websocket("/{document_id}")
async def websocket_endpoint(
    websocket: WebSocket, document_id: UUID, token: str | None = Query(None)
):
    user, shared_role = await authenticate_websocket(document_id, token)
    user_token = str(user.id) if user else str(id(websocket))
    username = user.username if user else "Anonymous"
    read_only = not (user or shared_role == ShareRole.EDIT)

    await manager.connect(websocket, document_id, username, user_token)

    listen_task = asyncio.create_task(
        forward_from_redis_to_websocket(websocket, document_id, user_token)
    )
    redis_client = await get_redis()

    try:
        while True:
            data = await websocket.receive_text()
            await process_websocket_message(
                data=data,
                websocket=websocket,
                redis_client=redis_client,
                document_id=document_id,
                user_token=user_token,
                read_only=read_only,
            )
    except WebSocketDisconnect:
        listen_task.cancel()
    finally:
        await manager.disconnect(websocket, document_id)
        await manager.broadcast(
            message={
                "message": f"User {user_token} Disconnected from the file.",
                "user_token": user_token,
            },
            websocket=websocket,
            document_id=document_id,
            user_token=user_token,
            send_to_owner=False,
        )
        await redis_client.close()
