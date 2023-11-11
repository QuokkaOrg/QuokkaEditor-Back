import json

from unittest.mock import patch, Mock
from unittest.mock import AsyncMock

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocket, WebSocketDisconnect

from quokka_editor_back.auth import auth_handler
from quokka_editor_back.models.document import Document
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


# TODO test forward_from_redis_to_websocket
@pytest.mark.skip("TODO")
@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
async def test_forward_from_redis_to_websocket(
    mock_redis, client: TestClient, active_user: UserLogin, document: Document, mocker
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    # mock_redis = AsyncMock(spec=Redis)
    # mocker.patch(
    #     "quokka_editor_back.routers.websockets.get_redis", return_value=mock_redis
    # )
    mock_pubsub = Mock()
    mock_pubsub.psubscribe.side_effect = AsyncMock()
    mock_pubsub.unsubscribe.side_effect = AsyncMock()
    mock_redis.return_value.pubsub = Mock(return_value=mock_pubsub)
    mock_pubsub.listen = AsyncMock(
        return_value=[{"type": "message", "data": "test_message"}]
    )

    # When
    # with patch("quokka_editor_back.utils.redis.get_redis") as mock_get_redis:
    await forward_from_redis_to_websocket(mocker.Mock(), document.id, token)

    mock_redis.pubsub.called_once_with()


@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
async def test_process_websocket_message_cursor(
    mock_redis, client: TestClient, active_user: UserLogin, document: Document, mocker
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    data = '{"type": "cursor"}'
    json_data = json.loads(data)
    new_data = json.dumps({"data": json_data, "user_token": token})
    mock_manager = AsyncMock(spec=manager)

    # When
    await process_websocket_message(
        data=data,
        websocket=mocker.Mock(),
        redis_client=mock_redis,
        document_id=document.id,
        user_token=token,
        read_only=False,
    )

    # Then
    mock_manager.broadcast.called_once_with(
        new_data,
        mocker.Mock(),
        document_id=document.id,
        send_to_owner=False,
        user_token=token,
    )
    mock_redis.rpush.assert_not_called()
    mock_redis.set.assert_not_called()


@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
async def test_process_websocket_message_read_only(
    mock_redis, client: TestClient, active_user: UserLogin, document: Document, mocker
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    data = '{"type": "message"}'
    mock_manager = AsyncMock(spec=manager)

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


@patch("quokka_editor_back.actors.transform_document", new_callable=AsyncMock)
@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
async def test_process_websocket_message(
    mock_document_transform,
    mock_redis,
    client: TestClient,
    active_user: UserLogin,
    document: Document,
    mocker,
):
    # Given
    token = auth_handler.encode_token(active_user.username)
    data = '{"type": "cursor"}'
    json_data = json.loads(data)
    new_data = json.dumps({"data": json_data, "user_token": token})
    mock_manager = AsyncMock(spec=manager)

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
    mock_redis.rpush.called_once_with(f"document_operations_{document.id}", new_data)
    mock_redis.set.called_once_with(f"document_processing_{document.id}", 1, nx=True)
    mock_document_transform.send.called_once_with(str(document.id))


async def test_websocket_properly_connect_and_disconnect(
    client: TestClient, active_user: UserLogin, document: Document
):
    # Given
    mock_manager = AsyncMock(spec=manager)
    token = auth_handler.encode_token(active_user.username)
    # When
    with client.websocket_connect(f"/ws/{document.id}?token={token}") as websocket:
        # Then
        mock_manager.connect.called_once_with(websocket, document.id)
        mock_manager.disconnect.called_once_with(websocket, document.id)


# TODO fix this test
@pytest.mark.skip("TODO")
@patch("quokka_editor_back.routers.websockets.process_websocket_message", side_effect=WebSocketDisconnect())
async def test_websocket_with_disconnect_error(
    client: TestClient, websocket, active_user: UserLogin, document: Document, mocker
):
    # Given
    mock_create_task = mocker.patch('asyncio.create_task', return_value=AsyncMock())
    mock_manager = AsyncMock(spec=manager)
    token = auth_handler.encode_token(active_user.username)

    # When
    with client.websocket_connect(f"/ws/{document.id}?token={token}"):
        mock_create_task.cancel.called_once_with()
        mock_manager.connect.called_once_with(mocker.Mock(), document.id)
        mock_manager.disconnect.called_once_with(mocker.Mock(), document.id)


async def test_websocket_authentication(
    client: TestClient, websocket, active_user: UserLogin, document: Document
):
    token = auth_handler.encode_token(active_user.username)
    with client.websocket_connect(f"/ws/{document.id}?token={token}"):
        with patch(
            "quokka_editor_back.routers.websockets.authenticate_websocket"
        ) as mock_authenticate_websocket:
            mock_authenticate_websocket.called_once_with(document.id, token)


@patch("quokka_editor_back.routers.websockets.get_redis", new_callable=AsyncMock)
async def test_get_redis(
    mock_get_redis,
    client: TestClient,
    websocket,
    active_user: UserLogin,
    document: Document,
):
    token = auth_handler.encode_token(active_user.username)
    with client.websocket_connect(f"/ws/{document.id}?token={token}"):
        mock_get_redis.called_once_with()
        mock_get_redis.close.called_once_with()


async def test_websocket_communication(
    client: TestClient, active_user: UserLogin, document: Document
):
    # Given
    mock_manager = AsyncMock(spec=manager)
    mock_websocket = AsyncMock(spec=WebSocket)
    token = auth_handler.encode_token(active_user.username)

    # When
    with client.websocket_connect(f"/ws/{document.id}?token={token}") as websocket:

        # Then
        mock_websocket.receive_text.called_once_with()
        mock_manager.broadcast.called_once_with(
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
