import json
import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from quokka_editor_back.models.document import Document, ShareRole
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.document import (
    DocumentUpdatePayload,
    ShareInput,
)


async def test_share_document(
    client: TestClient,
    document,
    mock_get_current_user,
):
    # Given
    document.shared_by_link = False
    document.shared_role = ShareRole.COMMENT
    await document.save()
    payload = ShareInput(shared_role=ShareRole.EDIT, shared_by_link=True)

    # When
    result = client.post(f"documents/share/{document.id}", json=payload.dict())

    # Then
    result_json = result.json()
    assert result.status_code == status.HTTP_201_CREATED
    assert result_json == {"message": f"Shared document {document.id}"}
    await document.refresh_from_db()
    assert document.shared_role == ShareRole.EDIT
    assert document.shared_by_link


async def test_share_document_unauthorized_user(
    client: TestClient,
    document,
):
    # Given
    payload = ShareInput(shared_role=ShareRole.EDIT, shared_by_link=True)

    # When
    result = client.post(f"documents/share/{document.id}", json=payload.dict())

    # Then
    assert result.status_code == status.HTTP_403_FORBIDDEN


async def test_share_document_no_document(
    client: TestClient,
    mock_get_current_user,
):
    # Given
    payload = ShareInput(shared_role=ShareRole.EDIT, shared_by_link=True)

    # When
    result = client.post("documents/share/test-id", json=payload.dict())

    # Then
    assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_check_searching(
    client: TestClient, mock_get_current_user, active_user, document
):
    # Given
    doc_1 = await Document.create(
        title="sample name",
        content=json.dumps(["test"]).encode(),
        user=active_user,
    )

    # When
    response = client.get("/documents/?search_phrase=sample")
    response_json = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response_json["items"]) == 1
    assert response_json["items"][0]["title"] == doc_1.title
    assert response_json["total"] == 1
    assert response_json["page"] == 1
    assert response_json["pages"] == 1


@pytest.mark.parametrize(
    "pagination_option, expected_value",
    [(1, 1), (10, 10), (20, 20), (50, 50), (100, 100)],
)
async def test_check_pagination(
    client: TestClient,
    mock_get_current_user,
    document,
    pagination_option,
    expected_value,
):
    # When
    response = client.get(f"/documents/?size={pagination_option}")
    response_json = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response_json["size"] == expected_value


@pytest.mark.parametrize("pagination_option", [-1, 0, 101])
async def test_check_invalid_pagination(
    client: TestClient,
    mock_get_current_user,
    pagination_option,
):
    # When
    response = client.get(f"/documents/?size={pagination_option}")

    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_check_size_page(
    client: TestClient, active_user, mock_get_current_user, document
):
    # Given
    await Document.create(
        title="sample name",
        content=json.dumps(["test"]).encode(),
        user=active_user,
    )

    # When
    response = client.get("/documents/?page=2&size=1")
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response["page"] == 2
    assert json_response["size"] == 1
    assert len(json_response["items"]) == 1


@pytest.mark.parametrize("page_number", [-1, 0])
async def test_check_invalid_page(
    client: TestClient, mock_get_current_user, page_number
):
    # When
    response = client.get(f"/documents/?page={page_number}")

    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_check_create_document(
    client: TestClient, mock_get_current_user, active_user: User
):
    # When
    response = client.post(url="/documents/")
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert json_response["title"] == "Draft Document"
    assert json_response["content"] == '[""]'
    assert json_response["user_id"] == str(active_user.id)


async def test_get_document_details(
    client: TestClient, document: Document, active_user: User, mocker
):
    mock = mocker.AsyncMock(return_value=active_user)
    mocked_get_current_user = mocker.patch(
        "quokka_editor_back.routers.documents.get_current_user", mock
    )
    # When
    response = client.get(
        url=f"/documents/{document.id}/", headers={"authorization": "Bearer Fake"}
    )
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response["title"] == "test_document"
    assert json_response["content"] == '["test"]'
    assert json_response["user_id"] == str(active_user.id)
    mocked_get_current_user.assert_called_once()


async def test_get_document_details_invalid_uuid(
    client: TestClient, mock_get_current_user, document: Document, active_user: User
):
    # When
    response = client.get(url=f"/documents/{uuid.uuid4()}/")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_document_details_invalid_post_method(
    client: TestClient, mock_get_current_user, active_user: User
):
    # When
    response = client.post(url=f"/documents/{uuid.uuid4()}/")

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


async def test_document_delete(
    client: TestClient, mock_get_current_user, document: Document, active_user: User
):
    # When
    response = client.delete(url=f"/documents/{document.id}/")

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_document_delete_invalid_id(
    client: TestClient, mock_get_current_user, active_user: User
):
    # Given
    document_uuid = uuid.uuid4()

    # When
    response = client.delete(url=f"/documents/{document_uuid}/")
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == f"Document {document_uuid} not found"


@pytest.mark.parametrize(
    "key, value, desired_response",
    [
        ("title", "new_value", "new_value"),
        ("content", ["test", "test"], json.dumps(["test", "test"])),
    ],
)
async def test_patch_document(
    client: TestClient,
    mock_get_current_user,
    document: Document,
    active_user: User,
    key: str,
    value: str,
    desired_response: str,
):
    # Given
    request_data = {key: value}

    # When
    response = client.patch(url=f"/documents/{document.id}/", json=request_data)
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response[key] == desired_response


async def test_patch_document_invalid_uuid(
    client: TestClient,
    mock_get_current_user,
    document: Document,
    active_user: User,
):
    # Given
    request_data = DocumentUpdatePayload(title="new_value")
    document_uuid = uuid.uuid4()

    # When
    response = client.patch(
        url=f"/documents/{document_uuid}/", json=request_data.dict()
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
