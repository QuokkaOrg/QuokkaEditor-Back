import json
import uuid

import pytest
from fastapi import status
from starlette.testclient import TestClient

from quokka_editor_back.models.document import DocumentTemplate
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.document_template import (
    DocumentTemplateCreatePayload,
    DocumentTemplateUpdatePayload,
)


@pytest.mark.parametrize(
    "title, content",
    [
        ("test", ["test", "test"]),
        ("", ["test", "test"]),
        ("", [""]),
    ],
)
async def test_create_document_template(
    client: TestClient, title, content, mock_get_current_user
):
    # Given
    payload = DocumentTemplateCreatePayload(title=title, content=content)

    # When
    response = client.post("templates/", json=payload.dict())
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert json_response["title"] == title
    assert json_response["content"] == json.dumps(content)


@pytest.mark.parametrize(
    "title, content",
    [
        (None, ["test", "test"]),
        ("test", None),
        (None, None),
    ],
)
async def test_invalid_data_document_template(
    client: TestClient, title, content, mock_get_current_user
):
    # Given
    payload = {"title": title, "content": content}

    # When
    response = client.post("templates/", json=payload)

    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_get_document_templates_list(
    client: TestClient, mock_get_current_user, document_template: DocumentTemplate
):
    # When
    response = client.get("templates/")
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response["total"] == 1
    assert len(json_response["items"]) == 1
    assert json_response["page"] == 1
    assert json_response["size"] == 50
    assert json_response["items"][0]["title"] == document_template.title
    assert json_response["items"][0]["content"] == document_template.content.decode()


@pytest.mark.parametrize(
    "pagination_option, expected_value",
    [(1, 1), (10, 10), (20, 20), (50, 50), (100, 100)],
)
async def test_check_pagination(
    client: TestClient,
    mock_get_current_user,
    document_template: DocumentTemplate,
    pagination_option: int,
    expected_value: int,
):
    # When
    response = client.get(f"/templates/?size={pagination_option}")
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
    response = client.get(f"/templates/?size={pagination_option}")

    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_check_size_page(
    client: TestClient,
    active_user: User,
    mock_get_current_user,
    document_template: DocumentTemplate,
):
    # Given
    await DocumentTemplate.create(
        title="sample_document_template",
        content=json.dumps(["sample", "document", "content"]).encode(),
    )

    # When
    response = client.get("/templates/?page=2&size=1")
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
    response = client.get(f"/templates/?page={page_number}")

    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_get_document_template_details(
    client: TestClient,
    mock_get_current_user,
    document_template: DocumentTemplate,
    active_user: User,
):
    # When
    response = client.get(url=f"/templates/{document_template.id}/")
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response["title"] == document_template.title
    assert json_response["content"] == document_template.content.decode()


async def test_get_document_template_details_invalid_uuid(
    client: TestClient,
    mock_get_current_user,
    document_template: DocumentTemplate,
    active_user: User,
):
    # When
    response = client.get(url=f"/templates/{uuid.uuid4()}/")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_document_template_details_invalid_post_method(
    client: TestClient, mock_get_current_user, active_user: User
):
    # When
    response = client.post(url=f"/templates/{uuid.uuid4()}/")

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


async def test_document_template_delete(
    client: TestClient,
    mock_get_current_user,
    document_template: DocumentTemplate,
    active_user: User,
):
    # When
    response = client.delete(url=f"/templates/{document_template.id}/")

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_document_template_delete_invalid_id(
    client: TestClient, mock_get_current_user, active_user: User
):
    # Given
    document_template_uuid = uuid.uuid4()

    # When
    response = client.delete(url=f"/templates/{document_template_uuid}/")
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        json_response["detail"]
        == f"Document Template{document_template_uuid} not found"
    )


@pytest.mark.parametrize(
    "key, value, desired_response",
    [
        ("title", "new_value", "new_value"),
        ("content", ["test", "test"], json.dumps(["test", "test"])),
    ],
)
async def test_patch_document_template(
    client: TestClient,
    mock_get_current_user,
    document_template: DocumentTemplate,
    active_user: User,
    key: str,
    value: str,
    desired_response: str,
):
    # Given
    request_data = {key: value}

    # When
    response = client.patch(
        url=f"/templates/{document_template.id}/", json=request_data
    )
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response[key] == desired_response


async def test_patch_document_template_invalid_uuid(
    client: TestClient,
    mock_get_current_user,
    active_user: User,
):
    # Given
    request_data = DocumentTemplateUpdatePayload(title="new_title")
    document_uuid = uuid.uuid4()

    # When
    response = client.patch(
        url=f"/templates/{document_uuid}/", json=request_data.dict()
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
