import json
import uuid
import logging
from unittest.mock import AsyncMock, Mock, patch, ANY

import pytest
import tortoise

from quokka_editor_back.actors.task import (
    fetch_operations_from_redis,
    decode_document_content,
    cleanup,
    apply_and_save_operation,
    transform_and_prepare_operation,
    async_document_task,
    process_one_operation,
    publish_operation,
    process_operations,
)
from quokka_editor_back.auth import auth_handler
from quokka_editor_back.models.document import Document
from quokka_editor_back.models.operation import (
    OperationSchema,
    PosSchema,
    OperationType,
    Operation,
)
from quokka_editor_back.models.user import User

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "content, desired_value",
    [
        (json.dumps({"key": "value"}).encode(), {"key": "value"}),
        (b"", {}),
    ],
)
def test_decode_document_content(content, desired_value):
    # Given
    document = Mock(content=content)

    # When
    decoded_content = decode_document_content(document)

    # Then
    assert decoded_content == desired_value


def test_decode_document_content_with_invalid_json():
    # Given
    document = Mock(content=b"invalid_data_here")

    # When
    with pytest.raises(json.JSONDecodeError):
        decode_document_content(document)


@patch("quokka_editor_back.actors.task.process_operations", new_callable=AsyncMock)
@patch("quokka_editor_back.actors.task.cleanup", new_callable=AsyncMock)
@patch("quokka_editor_back.actors.task.get_redis", new_callable=AsyncMock)
async def test_async_document_task(
    mocked_get_redis,
    mocked_cleanup,
    mocked_process_operations,
    active_user: User,
    document: Document,
):
    # When
    await async_document_task(str(document.id))

    # Then
    mocked_get_redis.assert_called_once()
    mocked_process_operations.assert_called_once_with(ANY, str(document.id), document)
    mocked_cleanup.assert_called_once_with(ANY, str(document.id))


@patch(
    "quokka_editor_back.actors.task.process_operations",
    side_effect=Exception("Message"),
)
@patch("quokka_editor_back.actors.task.cleanup", new_callable=AsyncMock)
@patch("quokka_editor_back.actors.task.get_redis", new_callable=AsyncMock)
async def test_async_document_task_exception(
    mocked_get_redis,
    mocked_cleanup,
    mocked_process_operations,
    active_user: User,
    document: Document,
    caplog,
):
    # When
    with caplog.at_level(logging.WARNING):
        await async_document_task(str(document.id))

    # Then
    assert "THERE IS AN ERROR Message" in caplog.text
    mocked_get_redis.assert_called_once()
    mocked_process_operations.assert_called_once()
    mocked_cleanup.assert_called_once_with(ANY, str(document.id))


class MockAsyncIterator:
    def __init__(self, data_list):
        self.data_list = data_list
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index < len(self.data_list):
            value = self.data_list[self.index]
            self.index += 1
            return value
        else:
            raise StopAsyncIteration


# TODO should be fixed.
async def test_process_operations(
    document: Document,
    mocker,
):
    # Given
    value_1 = "string"

    mock_op = OperationSchema(
        revision=3,
        from_pos=PosSchema(line=0, ch=0),
        to_pos=PosSchema(line=0, ch=0),
        text=["new text"],
        type=OperationType.INPUT.value,
    )
    redis_client_mock = mocker.patch("redis.asyncio", new_callable=AsyncMock)
    mocker.patch(
        "quokka_editor_back.actors.task.fetch_operations_from_redis",
        return_value=MockAsyncIterator([value_1]),
    )
    mocker.patch(
        "quokka_editor_back.actors.task.process_one_operation", return_value=mock_op
    )
    mocker.patch(
        "quokka_editor_back.actors.task.publish_operation", new_callable=AsyncMock
    )

    # When
    await process_operations(redis_client_mock, document)

    # Then


@patch(
    "quokka_editor_back.actors.task.apply_and_save_operation",
    new_callable=AsyncMock,
)
@patch(
    "quokka_editor_back.actors.task.transform_and_prepare_operation",
    new_callable=AsyncMock,
)
async def test_process_one_operation(
    mocked_transform_and_prepare_operation,
    mocked_apply_and_save_operation,
    document: Document,
):
    # Given
    op_data = {
        "from_pos": {"line": 0, "ch": 0},
        "to_pos": {"line": 0, "ch": 0},
        "text": ["text"],
        "type": OperationType.INPUT,
        "revision": 0,
        "data": "Test",
    }

    # When
    await process_one_operation(op_data, document)

    # Then
    mocked_transform_and_prepare_operation.asser_called_once_with(
        op_data["data"],
        document,
    )
    mocked_apply_and_save_operation.assert_called_once_with(ANY, document)


async def test_publish_operation(document: Document, active_user: User, mocker):
    # Given
    redis_client_mock = mocker.patch("redis.asyncio", new_callable=AsyncMock)
    token = auth_handler.encode_token(active_user.username)
    new_op = OperationSchema(
        revision=0,
        from_pos=PosSchema(line=0, ch=0),
        to_pos=PosSchema(line=0, ch=0),
        text=["new text"],
        type=OperationType.INPUT.value,
    )

    # When
    await publish_operation(redis_client_mock, document.id, token, new_op)

    # Then
    redis_client_mock.publish.assert_called_with(
        f"{document.id}_{token}",
        json.dumps(
            {
                "data": json.dumps({**new_op.dict(), "user_token": token}),
                "revision": new_op.revision,
            }
        ),
    )


async def test_fetch_operations_from_redis():
    # Given
    mock_redis_client = AsyncMock()
    redis_data = [b"data1", b"data2", b"data3"]
    mock_redis_client.lpop.side_effect = redis_data + [None]
    document_id = uuid.uuid4()

    # When
    result = [
        data
        async for data in fetch_operations_from_redis(mock_redis_client, document_id)
    ]

    # Then
    assert result == ["data1", "data2", "data3"]
    assert mock_redis_client.lpop.call_count == len(redis_data) + 1
    mock_redis_client.lpop.assert_called_with(f"document_operations_{document_id}")


async def test_fetch_operations_from_redis_with_empty_data():
    # Given
    mock_redis_client = AsyncMock()
    mock_redis_client.lpop.return_value = None

    # When
    result = [
        data
        async for data in fetch_operations_from_redis(
            mock_redis_client, "some_document_id"
        )
    ]

    # Then
    assert result == []
    assert mock_redis_client.lpop.call_count == 1


async def test_transform_and_prepare_operation(document: Document):
    # Given
    op_data = {
        "from_pos": {"line": 0, "ch": 0},
        "to_pos": {"line": 0, "ch": 0},
        "text": ["text"],
        "type": OperationType.INPUT,
        "revision": 0,
    }
    document.last_revision = 0
    # When
    result = await transform_and_prepare_operation(op_data, document)

    # Then
    assert result.revision == 1


async def test_transform_and_prepare_operation_document_revision_higher(
    document: Document,
):
    # Given
    op_data = {
        "from_pos": {"line": 0, "ch": 0},
        "to_pos": {"line": 0, "ch": 0},
        "text": ["text"],
        "type": OperationType.INPUT.value,
        "revision": 1,
    }
    to_pos = PosSchema(line=0, ch=0)
    from_pos = PosSchema(line=1, ch=1)
    operation = Operation(
        from_pos=from_pos.json(),
        to_pos=to_pos.json(),
        text=json.dumps(["new text"]),
        type=OperationType.INPUT.value,
        revision=2,
    )
    await operation.save()
    await document.operations.add(operation)
    document.last_revision = 2
    await document.save()

    with patch("quokka_editor_back.actors.task.transform") as mock_transform:
        mock_transform.return_value = OperationSchema(
            revision=2,
            from_pos=PosSchema(line=0, ch=0),
            to_pos=PosSchema(line=0, ch=0),
            text=["new text"],
            type=OperationType.INPUT.value,
        )

        # When
        result = await transform_and_prepare_operation(op_data, document)

    assert result is not None
    assert isinstance(result, OperationSchema)
    assert result.revision == 3

    mock_transform.assert_called_once_with(OperationSchema(**op_data), ANY)


async def test_apply_and_save_operation(document: Document, mocker):
    # Given
    data = "some test content"
    mocker.patch(
        "quokka_editor_back.actors.task.apply_operation",
        return_value=data,
    )
    to_pos = PosSchema(line=0, ch=0)
    from_pos = PosSchema(line=1, ch=1)
    op = OperationSchema(
        from_pos=from_pos,
        to_pos=to_pos,
        text=["new text"],
        type=OperationType.INPUT.value,
        revision=0,
    )

    # When
    await apply_and_save_operation(op, document)

    # Then
    await document.refresh_from_db()
    filtered_operations = await document.operations.filter(revision=op.revision)
    assert len(filtered_operations) == 1
    assert document.content == json.dumps(data).encode()


@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
async def test_cleanup_with_redis_error(mock_get_redis, mocker):
    # Given
    document_id = uuid.uuid4()
    mocker.patch("tortoise.connection.connections.close_all", return_value=Mock())

    # When
    await cleanup(mock_get_redis, document_id)

    # Then
    mock_get_redis.delete.assert_called_once_with(f"document_processing_{document_id}")
    tortoise.connections.close_all.assert_called_once_with()
