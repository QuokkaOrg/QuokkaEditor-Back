import logging
import uuid

from asgiref.sync import AsyncToSync
from redis.asyncio import Redis as AsyncRedis
from tortoise.connection import connections
from tortoise.transactions import in_transaction

from quokka_editor_back.models.operation import Operation, OperationType
from quokka_editor_back.routers.documents import OperationIn, get_document
from quokka_editor_back.utils.actors import dramatiq
from quokka_editor_back.utils.ot import apply_operation, transform
from quokka_editor_back.utils.redis import get_redis

logger = logging.getLogger(__name__)


def decode_document_content(document):
    return (document.content or b"").decode()


async def async_document_task(document_id, websocket_id, *args, **kwargs):
    redis_client: AsyncRedis = await get_redis()
    document = await get_document(document_id=uuid.UUID(document_id))
    async for op_data in fetch_operations_from_redis(redis_client, document_id):
        async with in_transaction():
            new_op = await transform_and_prepare_operation(op_data, document)
            await apply_and_save_operation(new_op, document)

        await redis_client.publish(f"{str(document_id)}_{websocket_id}", op_data)
    await cleanup(redis_client, document_id)


async def fetch_operations_from_redis(redis_client, document_id):
    while True:
        data = await redis_client.lpop(f"document_operations_{document_id}")
        if not data:
            break
        yield data.decode()


async def transform_and_prepare_operation(op_data: str, document):
    raw_new_op = OperationIn.parse_raw(op_data)

    if raw_new_op.type not in (OperationType.INSERT, OperationType.DELETE):
        logger.error("Invalid operation type")
        return None  # skip this operation

    new_op = Operation(**raw_new_op.dict())
    last_op = await document.operations.order_by("-revision").first()
    if last_op and new_op.revision <= last_op.revision:
        for prev_op in await document.operations.filter(revision__gte=new_op.revision):
            new_op = transform(new_op, prev_op)
        new_op.revision = last_op.revision + 1
    logger.debug(new_op.__dict__)
    return new_op


async def apply_and_save_operation(op, document):
    content = apply_operation(decode_document_content(document), op)
    await op.save()
    await document.operations.add(op)
    document.update_from_dict({"content": content.encode()})
    await document.save()


async def cleanup(redis_client, document_id):
    await connections.close_all()
    await redis_client.delete(f"document_processing_{document_id}")


class NamedAsyncToSync(AsyncToSync):
    __name__ = "transform_document"


sync_document_task = NamedAsyncToSync(async_document_task)
transform_document = dramatiq.actor(sync_document_task)
