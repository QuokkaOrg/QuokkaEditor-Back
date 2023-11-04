import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from quokka_editor_back.routers import manager


async def test_websocket_manager_connect(websocket: WebSocket):
    # Given
    document_id = uuid.uuid4()

    # When
    await manager.connect(websocket, document_id)

    # Then
    assert document_id in manager.active_connections
    assert websocket in manager.active_connections[document_id]


async def test_websocket_manager_disconnect(websocket: WebSocket):
    # Given
    document_id = uuid.uuid4()

    # When
    await manager.connect(websocket, document_id)
    manager.disconnect(websocket, document_id)

    # Then
    assert document_id in manager.active_connections
    assert websocket not in manager.active_connections[document_id]


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
        "message": message,
        "revision_log": revision,
        "user_token": user_token,
    }

    # When
    await manager.ack_message(websocket, message, revision, user_token)

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
    websocket: WebSocket, send_to_owner: str, revision: str
):
    # Given
    user_token = "user_token"
    document_id = uuid.uuid4()
    message = "Broadcast message"
    other_websocket = AsyncMock(spec=WebSocket)
    await manager.connect(websocket, document_id)
    await manager.connect(other_websocket, document_id)

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
        send_json_data = {
            "message": "ACK",
            "revision_log": revision,
            "user_token": user_token,
        }
        websocket.send_json.assert_called_once_with(send_json_data)
    other_websocket.send_text.assert_called_once_with(message)


async def test_websocket_manager_broadcast_without_not_required_fields(
    websocket: WebSocket
):
    # Given
    user_token = "user_token"
    document_id = uuid.uuid4()
    message = "Broadcast message"
    send_json_data = {
        "message": "ACK",
        "revision_log": None,
        "user_token": user_token,
    }
    other_websocket = AsyncMock(spec=WebSocket)
    await manager.connect(websocket, document_id)
    await manager.connect(other_websocket, document_id)

    # When
    await manager.broadcast(message, websocket, document_id, user_token=user_token)

    # Then
    websocket.send_text.assert_not_called()
    websocket.send_json.assert_called_once_with(send_json_data)
    other_websocket.send_text.assert_called_once_with(message)
