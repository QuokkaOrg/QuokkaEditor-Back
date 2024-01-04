import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from quokka_editor_back.models.user import User
from quokka_editor_back.routers import manager
from quokka_editor_back.schema.websocket import MessageTypeEnum


async def test_websocket_manager_connect(websocket: WebSocket, active_user: User):
    # Given
    user_token = "user_token"
    document_id = uuid.uuid4()

    # When
    await manager.connect(websocket, document_id, active_user.username, user_token)

    # Then
    assert document_id in manager.active_connections
    assert websocket in manager.active_connections[document_id]


async def test_websocket_manager_disconnect(websocket: WebSocket, active_user: User):
    # Given
    user_token = "user_token"
    document_id = uuid.uuid4()

    # When
    await manager.connect(websocket, document_id, active_user.username, user_token)
    await manager.disconnect(websocket, document_id)

    # Then
    assert document_id in manager.active_connections
    assert websocket not in manager.active_connections[document_id]


# TODO Delete this test and add send_all_users_info and broadcast_new_user tests
@pytest.mark.skip()
async def test_websocket_manager_send_personal_message(websocket: WebSocket):
    # Given
    message = "Hello, client!"

    # When
    await manager.send_personal_message(message, websocket)

    # Then
    websocket.send_text.assert_called_once_with(message)


async def test_websocket_manager_ack_message(websocket: WebSocket):
    # Given
    message = "ACK"
    revision = 1
    user_token = "user_token"
    expected_data = {
        "revision_log": revision,
        "user_token": user_token,
        "type": MessageTypeEnum.ACKNOWLEDGE,
    }
    # When
    await manager.ack_message(websocket, revision, user_token)

    # Then
    websocket.send_json.assert_called_once_with(expected_data)


@pytest.mark.parametrize(
    "send_to_owner, revision",
    [
        (True, 1),
        (False, 1),
        (None, 1),
        (False, None),
        (True, None),
        (None, None),
    ],
)
async def test_websocket_manager_broadcast(
    websocket: WebSocket, active_user: User, send_to_owner: str, revision: str
):
    # Given
    user_token = "user_token"
    document_id = uuid.uuid4()
    message = "Broadcast message"
    other_websocket = AsyncMock(spec=WebSocket)
    await manager.connect(websocket, document_id, active_user.username, user_token)
    await manager.connect(
        other_websocket, document_id, active_user.username, user_token
    )

    # When
    await manager.broadcast(
        message,
        websocket,
        document_id,
        user_token=user_token,
        revision=revision,
        send_to_owner=send_to_owner,
    )

    # Then
    websocket.send_text.assert_not_called()
    if send_to_owner:
        assert websocket.send_json.call_count == 3
    other_websocket.send_text.assert_not_called()


async def test_websocket_manager_broadcast_without_not_required_fields(
    websocket: WebSocket, active_user: User, mocker
):
    # Given
    user_token = "user_token"
    document_id = uuid.uuid4()
    message = "Broadcast message"
    send_json_data = {
        "revision_log": None,
        "user_token": user_token,
        "type": MessageTypeEnum.ACKNOWLEDGE,
    }
    mocker.patch(
        "quokka_editor_back.routers.connection_manager.rand_hex_color",
        return_value="some_color",
    )
    other_websocket_send_json_data = [
        {
            "username": "test_user",
            "user_token": "user_token",
            "clientColor": "some_color",
        }
    ]
    other_websocket = AsyncMock(spec=WebSocket)
    await manager.connect(websocket, document_id, active_user.username, user_token)
    await manager.connect(
        other_websocket, document_id, active_user.username, user_token
    )

    # When
    await manager.broadcast(message, websocket, document_id, user_token=user_token)

    # Then
    websocket.send_text.assert_not_called()
    websocket.send_json.assert_called_with(send_json_data)
    other_websocket.send_json.assert_called_once_with(other_websocket_send_json_data)
