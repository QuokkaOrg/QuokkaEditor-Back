import asyncio
import json
import logging
import uuid

from asgiref.sync import AsyncToSync
from redis.asyncio import Redis as AsyncRedis
from tortoise.connection import connections
from tortoise.transactions import in_transaction

from quokka_editor_back.models.document import Document
from quokka_editor_back.models.operation import (
    Operation,
    OperationSchema,
    OperationType,
    PosSchema,
)
from quokka_editor_back.routers.documents import get_document
from quokka_editor_back.utils.actors import dramatiq
from quokka_editor_back.utils.ot import apply_operation
from quokka_editor_back.utils.redis import get_redis

logger = logging.getLogger(__name__)


def decode_document_content(document):
    return json.loads((document.content or b"").decode())


async def async_document_task(
    document_id: str, websocket_id: str, *args, **kwargs
) -> None:
    redis_client: AsyncRedis = await get_redis()
    try:
        document = await get_document(document_id=uuid.UUID(document_id))
        async for op_data in fetch_operations_from_redis(redis_client, document_id):
            async with in_transaction():
                new_op = await transform_and_prepare_operation(op_data, document)
                if not new_op:
                    break
                await apply_and_save_operation(new_op, document)

            await redis_client.publish(f"{str(document_id)}_{websocket_id}", op_data)
    except Exception as err:
        logger.warning(err)
    finally:
        await cleanup(redis_client, document_id)


async def fetch_operations_from_redis(redis_client: AsyncRedis, document_id: str):
    while True:
        data = await redis_client.lpop(f"document_operations_{document_id}")  # type: ignore
        if not data:
            break
        yield data.decode()  # type:ignore


async def transform_and_prepare_operation(
    op_data: str, document: Document
) -> OperationSchema | None:
    new_op = OperationSchema.parse_raw(op_data)

    if new_op.type.value not in OperationType.list():
        logger.error("Invalid operation type")
        return None  # skip this operation

    # TODO: adjust to the new operation type
    # last_op = await document.operations.order_by("-revision").first()
    # if last_op and new_op.revision <= last_op.revision:
    #     for prev_op in await document.operations.filter(revision__gte=new_op.revision):
    #         new_op = transform(new_op, prev_op)
    #     new_op.revision = last_op.revision + 1
    logger.debug(new_op.__dict__)
    return new_op


async def apply_and_save_operation(op: OperationSchema, document: Document) -> None:
    content = apply_operation(decode_document_content(document), op)
    new_op = Operation(
        from_pos=op.from_pos.json(),
        to_pos=op.to_pos.json(),
        text=json.dumps(op.text),
        type=op.type,
        revision=op.revision,
    )

    await new_op.save()
    await document.operations.add(new_op)
    document.update_from_dict({"content": json.dumps(content).encode()})
    await document.save()


async def cleanup(redis_client: AsyncRedis, document_id: str) -> None:
    await connections.close_all()
    await redis_client.delete(f"document_processing_{document_id}")


class NamedAsyncToSync(AsyncToSync):
    __name__ = "transform_document"


sync_document_task = NamedAsyncToSync(async_document_task)
transform_document = dramatiq.actor(sync_document_task, max_retries=1)
