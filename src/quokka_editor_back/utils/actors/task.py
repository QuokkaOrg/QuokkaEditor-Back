from tortoise import Tortoise

from quokka_editor_back.models.operation import Operation, OperationType
from quokka_editor_back.routers.documents import OperationIn, get_document

from quokka_editor_back.settings import TORTOISE_ORM

from quokka_editor_back.utils.ot import apply_operation, transform
from quokka_editor_back.utils.redis import get_redis
from quokka_editor_back.utils.actors import dramatiq
from quokka_editor_back.utils.time_execution import timed_execution
from quokka_editor_back.routers import manager
from asgiref.sync import AsyncToSync, async_to_sync
from asyncio import sleep
import uuid
from datetime import datetime
from tortoise.connection import connections
import logging
from redis.asyncio.lock import Lock

LOCKED_VALUE = "true"
UNLOCKED_VALUE = "unlocked"

logger = logging.getLogger(__name__)


async def async_document_task(document_id, websocket_id, *args, **kwargs):
    redis_client = await get_redis()
    while True:
        data = await redis_client.lpop(f"document_operations_{document_id}")
        if not data:
            break

        try:
            with timed_execution():
                await Tortoise.init(config=TORTOISE_ORM)
                document = await get_document(document_id=uuid.UUID(document_id))

                op_in = OperationIn.parse_raw(data.decode())
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
    await redis_client.delete(f"document_processing_{document_id}")


class NamedAsyncToSync(AsyncToSync):
    __name__ = "transform_document"


sync_document_task = NamedAsyncToSync(async_document_task)
transform_document = dramatiq.actor(sync_document_task)
