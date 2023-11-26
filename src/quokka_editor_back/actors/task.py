import json
import logging
import uuid

from asgiref.sync import AsyncToSync
from redis.asyncio import Redis as AsyncRedis
from tortoise.connection import connections
from tortoise.transactions import in_transaction

from quokka_editor_back.actors import dramatiq
from quokka_editor_back.models.document import Document
from quokka_editor_back.models.operation import (
    Operation,
    OperationSchema,
    OperationType,
    PosSchema,
)
from quokka_editor_back.routers.documents import get_document
from quokka_editor_back.schema.websocket import MessageTypeEnum
from quokka_editor_back.utils.ot import apply_operation, transform
from quokka_editor_back.utils.redis import get_redis

logger = logging.getLogger(__name__)


def decode_document_content(document):
    return json.loads((document.content or b"").decode())


async def async_document_task(document_id: str, *args, **kwargs) -> None:
    redis_client: AsyncRedis = await get_redis()
    try:
        document = await get_document(document_id=uuid.UUID(document_id))
        await process_operations(redis_client, document_id, document)
    except Exception as err:
        logger.warning("THERE  IS AN ERROR %s", err)
    finally:
        await cleanup(redis_client, document_id)


async def process_one_operation(
    loaded_op_data: dict, document: Document
) -> OperationSchema | None:
    async with in_transaction():
        new_op = await transform_and_prepare_operation(
            loaded_op_data["data"],
            document,
        )
        if not new_op:
            return
        await apply_and_save_operation(new_op, document)
    return new_op


async def process_operations(
    redis_client: AsyncRedis, document_id: str, document: Document
) -> None:
    async for op_data in fetch_operations_from_redis(redis_client, document_id):
        loaded_op_data = json.loads(op_data)
        user_token = loaded_op_data["user_token"]
        if new_op := await process_one_operation(loaded_op_data, document):
            await publish_operation(
                redis_client,
                document_id,
                user_token,
                new_op,
            )


async def publish_operation(
    redis_client: AsyncRedis,
    document_id: str,
    user_token: str,
    new_op: OperationSchema,
) -> None:
    await redis_client.publish(
        f"{document_id}_{user_token}",
        json.dumps(
            {
                "data": new_op.dict(),
                "type": MessageTypeEnum.EXT_CHANGE,
                "user_token": user_token,
                "revision": new_op.revision,
            }
        ),
    )


async def fetch_operations_from_redis(redis_client: AsyncRedis, document_id: str):
    while True:
        data = await redis_client.lpop(f"document_operations_{document_id}")  # type: ignore
        if not data:
            break
        yield data.decode()  # type:ignore


async def transform_and_prepare_operation(
    op_data: dict, document: Document
) -> OperationSchema | None:
    new_op = OperationSchema(**op_data)

    if new_op.type.value not in OperationType.list():
        logger.error("Invalid operation type")
        return None  # skip this operation

    if new_op.revision < document.last_revision:
        for prev_op in await document.operations.filter(revision__gt=new_op.revision):
            prev_op_schema = OperationSchema(
                from_pos=PosSchema.parse_raw(
                    prev_op.from_pos,
                ),
                to_pos=PosSchema.parse_raw(
                    prev_op.to_pos,
                ),
                text=json.loads(prev_op.text),
                type=prev_op.type,
                revision=prev_op.revision,
            )
            new_op = transform(new_op, prev_op_schema)
    new_op.revision = document.last_revision + 1
    return new_op


async def apply_and_save_operation(op: OperationSchema, document: Document) -> None:
    content = apply_operation(decode_document_content(document), op)
    document.update_from_dict({"last_revision": op.revision})
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
    await redis_client.delete(f"document_processing_{document_id}")
    await connections.close_all()


class NamedAsyncToSync(AsyncToSync):
    __name__ = "transform_document"


sync_document_task = NamedAsyncToSync(async_document_task)
transform_document = dramatiq.actor(sync_document_task, max_retries=1)
