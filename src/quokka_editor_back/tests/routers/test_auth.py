import pytest
from starlette import status
from starlette.testclient import TestClient

from quokka_editor_back.auth import auth_handler
from quokka_editor_back.models.user import User


def test_user_register(client: TestClient):
    # Given
    user_data = {
        "username": "test_user",
        "email": "test@user.com",
        "password": "test_passwd",
    }

    # When
    response = client.post("auth/register/", json=user_data)
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert json_response is None


@pytest.mark.parametrize("email", ["test", "@test", "test@c", "test@.c", "test@co."])
def test_invalid_email_format(client: TestClient, email: str):
    # Given
    user_data = {
        "username": "test_user",
        "email": email,
        "password": "test_passwd",
    }
    # When
    result = client.post("auth/register/", json=user_data)

    # Then
    assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_user_already_exist(client: TestClient, active_user: User):
    # Given
    user_data = {
        "username": "test_user",
        "email": "test@user.com",
        "password": "test_passwd",
    }

    # When
    response = client.post("auth/register/", json=user_data)
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert json_response["detail"] == "User already exists"


async def test_login_user(client: TestClient, active_user: User):
    # Given
    user_data = {
        "username": active_user.username,
        "password": "super_secret_password",
    }

    # When
    response = client.post("auth/login/", json=user_data)
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response["token"] == auth_handler.encode_token(active_user.username)


@pytest.mark.parametrize(
    "key, value", [("username", "invalid"), ("password", "invalid")]
)
async def test_login_user_invalid_data(
    client: TestClient, active_user: User, key: str, value: str
):
    # Given
    user_data = {
        "username": "test_user",
        "password": "super_secret_password",
    }
    user_data[key] = value

    # When
    response = client.post("auth/login/", json=user_data)
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert json_response["detail"] == f"Invalid {key}"


async def test_login_user_invalid_get_method(client: TestClient):
    # When
    response = client.get("auth/login/")

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


async def test_refresh_token(client: TestClient, mock_security, auth_token):
    # When
    response = client.get("auth/refresh/")
    json_response = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert json_response == auth_handler.refresh_token(auth_token)


async def test_refresh_token_invalid_post_method(client: TestClient):
    # When
    response = client.post("auth/refresh/", json={})

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
