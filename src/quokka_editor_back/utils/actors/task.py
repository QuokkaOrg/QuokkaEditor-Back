from tortoise import Tortoise

from quokka_editor_back.models.operation import Operation, OperationType
from quokka_editor_back.routers.documents import OperationIn, get_document

from quokka_editor_back.settings import TORTOISE_ORM

from quokka_editor_back.utils.ot import apply_operation, transform
from quokka_editor_back.utils.time_execution import timed_execution
from quokka_editor_back.routers import manager
from asgiref.sync import AsyncToSync

import uuid
from time import sleep
from quokka_editor_back.utils.actors import dramatiq

from tortoise.connection import connections


async def async_document_task(
    document_id,
    data,
):
    await Tortoise.init(config=TORTOISE_ORM)

    print(document_id)

    document = await get_document(document_id=uuid.UUID(document_id))

    op_in = OperationIn.parse_raw(data)
    with timed_execution():
        content = (document.content or b"").decode()
        print(op_in)
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
            for prev_op in await document.operations.filter(revision__gte=op.revision):
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
        # await manager.ack_message(websocket, "ACK", 1)
        await manager.broadcast(op_in.json())
    await connections.close_all()


class NamedAsyncToSync(AsyncToSync):
    __name__ = "transform_document"


sync_document_task = NamedAsyncToSync(async_document_task)
transform_document = dramatiq.actor(sync_document_task)


@dramatiq.actor
def process_data(data: dict):
    print(f"Start: {data}")
    sleep(data["sleep_int"])
    print(f"Processing: {data}")
