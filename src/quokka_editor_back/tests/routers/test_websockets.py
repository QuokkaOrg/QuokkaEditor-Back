import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocket, WebSocketDisconnect

from quokka_editor_back.auth import auth_handler
from quokka_editor_back.models.document import Document, ShareRole
from quokka_editor_back.routers import manager
from quokka_editor_back.routers.websockets import (
    decode_redis_message,
    forward_from_redis_to_websocket,
    process_websocket_message,
)
from quokka_editor_back.schema.auth import UserLogin


async def test_decode_redis_message():
    # Given
    message = {"data": b'{"key": "value"}'}

    # When
    result = decode_redis_message(message)

    # Then
    assert result == {"key": "value"}


class AsyncIterator:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


async def test_subscribe_channel_and_broadcast_redis_messages():
    pass


@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
async def test_forward_from_redis_to_websocket(
    mocked_get_redis,
    client: TestClient,
    active_user: UserLogin,
    document: Document,
    mocker,
):
    # Given
    mocked_subscribe_channel_and_broadcast_redis_messages = mocker.patch(
        "quokka_editor_back.routers.websockets.subscribe_channel_and_broadcast_redis_messages",
        new_callable=AsyncMock,
    )
    pubsub_mock = AsyncMock()
    close_mock = AsyncMock()
    mocked_get_redis.return_value.pubsub = pubsub_mock
    mocked_get_redis.return_value.close = close_mock
    token = auth_handler.encode_token(active_user.username)

    # When
    await forward_from_redis_to_websocket(mocker.Mock(), document.id, token)

    # Then
    mocked_get_redis.assert_called_once()
    mocked_subscribe_channel_and_broadcast_redis_messages.assert_called_once()
    pubsub_mock.assert_called_once()
    close_mock.assert_called_once()


async def test_process_websocket_message_cursor(
    active_user: UserLogin, document: Document, mocker
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    data = '{"type": "cursor"}'
    json_data = json.loads(data)
    new_data = json.dumps({"data": json_data, "user_token": token})
    mock_manager = AsyncMock()
    mocked_manager = mocker.patch(
        "quokka_editor_back.routers.websockets.manager", mock_manager
    )
    redis_client_mock = mocker.patch("redis.asyncio", new_callable=AsyncMock)
    websocket_mock = mocker.Mock()

    # When
    await process_websocket_message(
        data=data,
        websocket=websocket_mock,
        redis_client=redis_client_mock,
        document_id=document.id,
        user_token=token,
        read_only=False,
    )

    # Then
    mocked_manager.broadcast.assert_called_once_with(
        new_data,
        websocket_mock,
        document_id=document.id,
        send_to_owner=False,
        user_token=token,
    )
    redis_client_mock.rpush.assert_not_called()
    redis_client_mock.set.assert_not_called()


@patch("quokka_editor_back.actors.transform_document.send", new_callable=AsyncMock)
async def test_process_websocket_message(
    mock_transform_document_send,
    client: TestClient,
    active_user: UserLogin,
    document: Document,
    mocker,
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    data = '{"type": "message"}'
    json_data = json.loads(data)
    new_data = json.dumps({"data": json_data, "user_token": token})
    mock_manager = AsyncMock()
    redis_client_mock = mocker.patch("redis.asyncio", new_callable=AsyncMock)

    # When
    await process_websocket_message(
        data=data,
        websocket=mocker.Mock(),
        redis_client=redis_client_mock,
        document_id=document.id,
        user_token=token,
        read_only=False,
    )

    # Then
    mock_manager.broadcast.assert_not_called()
    redis_client_mock.rpush.assert_called_once_with(
        f"document_operations_{document.id}", new_data
    )
    redis_client_mock.set.assert_called_once_with(
        f"document_processing_{document.id}", 1, nx=True
    )
    mock_transform_document_send.assert_called_once_with(str(document.id))


@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
async def test_process_websocket_message_read_only(
    mock_redis, client: TestClient, active_user: UserLogin, document: Document, mocker
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    data = '{"type": "message"}'
    mock_manager = AsyncMock()

    # When
    await process_websocket_message(
        data=data,
        websocket=mocker.Mock(),
        redis_client=mock_redis,
        document_id=document.id,
        user_token=token,
        read_only=True,
    )

    # Then
    mock_manager.broadcast.assert_not_called()
    mock_redis.rpush.assert_not_called()
    mock_redis.set.assert_not_called()


@pytest.mark.skip("Testing the websocket connection will be fixed later")
@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
@patch(
    "quokka_editor_back.routers.websockets.process_websocket_message",
    side_effect=WebSocketDisconnect,
)
async def test_websocket_properly_connect_and_disconnect(
    mocked_process_websocket_message,
    mocked_get_redis,
    client: TestClient,
    active_user: UserLogin,
    document: Document,
    mocker,
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    close_mock = AsyncMock()
    mocked_get_redis.return_value.close = close_mock
    mock_manager = Mock()
    mock_manager.connect = AsyncMock()
    mock_manager.broadcast = AsyncMock()
    mocked_manager = mocker.patch(
        "quokka_editor_back.routers.websockets.manager", mock_manager
    )
    mocker.patch("asyncio.create_task", mock_manager)
    mocker.patch(
        "quokka_editor_back.routers.websockets.forward_from_redis_to_websocket",
        mock_manager,
    )

    # When
    with client.websocket_connect(f"/ws/{document.id}?token={token}") as websocket:
        # Then
        websocket.send_json({"data": "data"})
        mocked_manager.connect.assert_called_once_with(websocket, document.id)
        mocked_manager.broadcast.assert_called_once_with(
            message=json.dumps(
                {
                    "message": f"User {token} Disconnected from the file.",
                    "user_token": token,
                }
            ),
            websocket=websocket,
            document_id=document.id,
            user_token=token,
            send_to_owner=False,
        )
        close_mock.assert_called_once()
        mocked_manager.disconnect.assert_called_once_with(websocket, document.id)


@pytest.mark.skip("Testing the websocket connection will be fixed later")
@patch("quokka_editor_back.actors.transform_document", new_callable=AsyncMock)
@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
@patch(
    "quokka_editor_back.routers.websockets.process_websocket_message",
    side_effect=Exception("Message"),
)
async def test_websocket_with_disconnect_error(
    mocked_process_websocket_message,
    mocked_get_redis,
    mocked_transform_document,
    client: TestClient,
    websocket,
    active_user: UserLogin,
    document: Document,
    mocker,
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    mock_manager = AsyncMock(spec=manager)

    # When
    with client.websocket_connect(f"/ws/{document.id}?token={token}"):
        mocked_manager = mocker.patch(
            "quokka_editor_back.routers.websockets.manager", new_callable=mock_manager
        )

        mocked_manager.connect.assert_called_once_with(mocker.Mock(), document.id)
        mocked_manager.disconnect.assert_called_once_with(mocker.Mock(), document.id)


@pytest.mark.skip("Testing the websocket connection will be fixed later")
async def test_websocket_authentication(
    client: TestClient, websocket, active_user: UserLogin, document: Document, mocker
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    mock_authenticate_websocket = mocker.patch(
        "quokka_editor_back.routers.websockets.authenticate_websocket",
        new_callable=AsyncMock(return_value=(123, ShareRole.EDIT)),
    )

    # When
    with client.websocket_connect(f"/ws/{document.id}?token={token}"):
        # Then
        mock_authenticate_websocket.assert_called_once_with(document.id, token)


@pytest.mark.skip("Testing the websocket connection will be fixed later")
async def test_websocket_communication(
    client: TestClient, active_user: UserLogin, document: Document, mocker
):
    # Given
    AsyncMock(spec=WebSocket)
    mocked_manager_broadcast = mocker.patch(
        "quokka_editor_back.routers.websockets.manager.broadcast", AsyncMock()
    )
    token = auth_handler.encode_token(active_user.username)

    # When
    with client.websocket_connect(f"/ws/{document.id}?token={token}") as websocket:
        # Then
        mocked_manager_broadcast.assert_called_once_with(
            message=json.dumps(
                {
                    "message": f"User {token} Disconnected from the file.",
                    "user_token": token,
                }
            ),
            websocket=websocket,
            document_id=document.id,
            user_token=token,
            send_to_owner=False,
        )


@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
async def test_get_redis(
    mocked_get_redis,
    client: TestClient,
    websocket,
    active_user: UserLogin,
    document: Document,
):
    close_mock = AsyncMock()
    mocked_get_redis.return_value.close = close_mock
    token = auth_handler.encode_token(active_user.username)
    with client.websocket_connect(f"/ws/{document.id}?token={token}"):
        assert mocked_get_redis.call_count == 2
    close_mock.assert_called_once()
