from tortoise import Tortoise

from quokka_editor_back.models.operation import Operation, OperationType
from quokka_editor_back.routers.documents import OperationIn, get_document

from quokka_editor_back.settings import TORTOISE_ORM

from quokka_editor_back.utils.ot import apply_operation, transform
from quokka_editor_back.utils.redis import get_redis
from quokka_editor_back.utils.time_execution import timed_execution
from quokka_editor_back.routers import manager
from asgiref.sync import AsyncToSync, async_to_sync
from asyncio import sleep
import uuid
from quokka_editor_back.utils.actors import dramatiq
from datetime import datetime
from tortoise.connection import connections
import logging

LOCKED_VALUE = "true"
UNLOCKED_VALUE = "unlocked"

logger = logging.getLogger(__name__)


def generate_redis_key(prefix, identifier):
    return f"{prefix}_{identifier}"


async def wait_in_line_and_for_notification(
    redis, queue_key: str, notification_key: str, worker_id: str, data
):
    # Dodaj swój worker_id do kolejki
    await redis.lpush(queue_key, worker_id)
    logger.info("wait_in_line_and_for_notification %s %s", str(data), str(worker_id))

    # Pobierz pierwszy worker z kolejki
    first_in_line = await redis.lindex(queue_key, -1)

    # Jeśli worker nie jest pierwszy w kolejce, czeka na powiadomienie
    if first_in_line and first_in_line.decode("utf-8") != worker_id:
        logger.info(
            "Worker %s waiting for %s in line %s",
            str(worker_id),
            str(first_in_line),
            str(data),
        )
        await redis.brpop(generate_redis_key(notification_key, worker_id))


async def release_lock(redis, worker_id, notification_key, queue_key, data) -> None:
    # Usuń siebie z kolejki
    await redis.lrem(queue_key, 1, worker_id)
    logger.info("release_lock %s %s", str(worker_id), str(data))
    # Powiadom następnego workera w kolejce (jeśli istnieje)
    next_in_line = await redis.lindex(queue_key, -1)
    if next_in_line:
        await redis.lpush(
            generate_redis_key(notification_key, next_in_line.decode("utf-8")),
            "unlocked",
        )


async def async_document_task(
    document_id,
    websocket_id,
    data,
):
    redis_client = await get_redis()
    notification_key = generate_redis_key("document_notification", document_id)
    queue_key = generate_redis_key("document_queue", document_id)
    worker_id = str(uuid.uuid4())

    await wait_in_line_and_for_notification(
        redis_client, queue_key, notification_key, worker_id, data
    )

    try:
        with timed_execution():
            await Tortoise.init(config=TORTOISE_ORM)
            document = await get_document(document_id=uuid.UUID(document_id))

            op_in = OperationIn.parse_raw(data)
            content = (document.content or b"").decode()

            if op_in.type in (OperationType.INSERT, OperationType.DELETE):
                op = Operation(
                    pos=op_in.pos,
                    content=op_in.char,
                    type=op_in.type,
                    revision=op_in.revision,
                )
            else:
                print("invalid operation type")
                # TODO: USE LOGGER AND DO NOT RAISE EXC
                # raise HTTPException(status_code=400, detail="Invalid operation type")

            # Transform operation
            last_op = await document.operations.order_by("-revision").first()
            if last_op and op.revision <= last_op.revision:
                op.revision = last_op.revision + 1
                for prev_op in await document.operations.filter(
                    revision__gte=op.revision
                ):
                    op = transform(op, prev_op)

            # Apply operation
            content = apply_operation(content, op)

            # Save operation
            # document.recent_revision = last_op
            # op.revision = 0
            await op.save()
            await document.operations.add(op)
            document.update_from_dict({"content": content.encode()})
            await document.save()
            await redis_client.publish(f"{str(document_id)}_{websocket_id}", data)
        await connections.close_all()
    except Exception as e:
        logger.error(f"Error processing document task: {e}")
    finally:
        await release_lock(redis_client, worker_id, notification_key, queue_key, data)


class NamedAsyncToSync(AsyncToSync):
    __name__ = "transform_document"


sync_document_task = NamedAsyncToSync(async_document_task)
transform_document = dramatiq.actor(sync_document_task)
