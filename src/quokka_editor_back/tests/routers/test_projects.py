import uuid

import pytest
from fastapi import status
from starlette.testclient import TestClient

from quokka_editor_back.models.project import Project, ShareRole
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.project import ShareInput


async def test_share_project(
    client: TestClient,
    project,
    mock_get_current_user,
):
    # Given
    project.shared_by_link = False
    project.shared_role = ShareRole.COMMENT
    await project.save()
    payload = ShareInput(shared_role=ShareRole.EDIT, shared_by_link=True)

    # When
    result = client.post(f"projects/share/{project.id}", json=payload.dict())

    # Then
    result_json = result.json()
    assert result.status_code == status.HTTP_201_CREATED
    assert result_json == {"message": f"Shared project {project.id}"}
    await project.refresh_from_db()
    assert project.shared_role == ShareRole.EDIT
    assert project.shared_by_link


async def test_share_project_unauthorized_user(
    client: TestClient,
    project,
):
    # Given
    payload = ShareInput(shared_role=ShareRole.EDIT, shared_by_link=True)

    # When
    result = client.post(f"projects/share/{project.id}", json=payload.dict())

    # Then
    assert result.status_code == status.HTTP_403_FORBIDDEN


async def test_share_project_no_project(
    client: TestClient,
    mock_get_current_user,
):
    # Given
    payload = ShareInput(shared_role=ShareRole.EDIT, shared_by_link=True)

    # When
    result = client.post("projects/share/test-id", json=payload.dict())

    # Then
    assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "pagination_option, expected_value",
    [(1, 1), (10, 10), (20, 20), (50, 50), (100, 100)],
)
async def test_check_pagination(
    client: TestClient,
    mock_get_current_user,
    pagination_option,
    expected_value,
):
    # When
    response = client.get(f"projects/?size={pagination_option}")
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
    response = client.get(f"projects/?size={pagination_option}")

    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_check_size_page1(
    client: TestClient, project: Project, active_user: User, mock_get_current_user
):
    # Given
    await Project.create(
        user_id=active_user.id,
        title="sample name",
    )

    # When
    response = client.get(
        "projects/?page=2&size=1", headers={"authorization": "Bearer Fake"}
    )
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response["page"] == 2
    assert json_response["size"] == 1
    assert len(json_response["items"]) == 1


@pytest.mark.parametrize("page_number", [-1, 0])
async def test_check_invalid_page(
    client: TestClient, mock_get_current_user, page_number: int
):
    # When
    response = client.get(f"projects/?page={page_number}")

    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_check_create_project(
    client: TestClient, mock_get_current_user, active_user: User
):
    # Given
    project_title = "test_name"

    # When
    response = client.post(url="projects/", json={"title": project_title})
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert json_response["title"] == project_title
    assert json_response["user_id"] == str(active_user.id)


async def test_get_project_details(
    client: TestClient, project: Project, active_user: User, mocker
):
    # Given
    mock = mocker.AsyncMock(return_value=active_user)
    mocker.patch("quokka_editor_back.routers.projects.get_current_user", mock)

    # When
    response = client.get(
        url=f"projects/{project.id}/", headers={"authorization": "Bearer Fake"}
    )
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response["project"]["title"] == project.title
    assert json_response["project"]["id"] == str(project.id)
    assert json_response["project"]["user_id"] == str(active_user.id)
    assert json_response["project"]["images"] == project.images
    assert json_response["project"]["shared_role"] == project.shared_role
    assert len(json_response["documents"]) == 0


async def test_get_project_details_invalid_uuid(
    client: TestClient, mock_get_current_user, project: Project, active_user: User
):
    # When
    response = client.get(url=f"projects/{uuid.uuid4()}/")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_project_details_invalid_post_method(
    client: TestClient, mock_get_current_user, active_user: User
):
    # When
    response = client.post(url=f"projects/{uuid.uuid4()}/")

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


async def test_project_delete(
    client: TestClient, mock_get_current_user, project: Project, active_user: User
):
    # When
    response = client.delete(url=f"projects/{project.id}/")

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_project_delete_invalid_id(
    client: TestClient, mock_get_current_user, active_user: User
):
    # Given
    project_uuid = uuid.uuid4()

    # When
    response = client.delete(url=f"projects/{project_uuid}/")
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == f"Project {project_uuid} not found"


async def test_patch_project(
    client: TestClient,
    mock_get_current_user,
    project: Project,
    active_user: User,
):
    # Given
    request_data = {"title": "new_value"}

    # When
    response = client.patch(url=f"projects/{project.id}/", json=request_data)
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response["title"] == "new_value"


async def test_patch_project_invalid_uuid(
    client: TestClient,
    mock_get_current_user,
    project: Project,
    active_user: User,
):
    # Given
    request_data = {"title": "new_value"}
    project_uuid = uuid.uuid4()

    # When
    response = client.patch(url=f"projects/{project_uuid}/", json=request_data)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
