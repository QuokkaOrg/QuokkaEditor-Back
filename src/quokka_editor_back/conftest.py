import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from tortoise import Tortoise
from tortoise.backends.base.config_generator import generate_config
from tortoise.contrib.test import _init_db

from quokka_editor_back.app import app as asgi_app
from quokka_editor_back.auth import auth_handler
from quokka_editor_back.auth.utils import get_current_user
from quokka_editor_back.models.document import Document, DocumentTemplate
from quokka_editor_back.models.user import User
from quokka_editor_back.settings import TORTOISE_ORM


@pytest.fixture
async def fastapi_app():
    return asgi_app


@pytest.fixture(autouse=True)
async def initialize_tests(request):
    await _init_db(
        generate_config(
            "sqlite:///tmp/test-{}.sqlite",
            app_modules={
                "quokka_editor_back": TORTOISE_ORM["apps"]["quokka_editor_back"][
                    "models"
                ]
            },
            testing=True,
            connection_label="quokka_editor_back",
        )
    )
    yield
    await Tortoise._drop_databases()


@pytest.fixture
async def client() -> TestClient:
    return TestClient(app=asgi_app)


@pytest.fixture
async def active_user() -> User:
    return await User.create(
        username="test_user",
        email="test@test.com",
        first_name="tester",
        last_name="test",
        hashed_password=auth_handler.encode_password(SecretStr("super_secret_password")),
        is_active=True,
    )


@pytest.fixture
async def document(active_user: User) -> Document:
    return await Document.create(
        title="test_document",
        content=json.dumps(["test"]).encode(),
        user=active_user,
    )


@pytest.fixture
async def document_template() -> DocumentTemplate:
    return await DocumentTemplate.create(
        title="test_document_template",
        content=json.dumps(["sample", "text"]).encode()
    )


@pytest.fixture
async def mock_get_current_user(fastapi_app: FastAPI, active_user: User):
    fastapi_app.dependency_overrides[get_current_user] = lambda: active_user
    yield
    fastapi_app.dependency_overrides.pop(get_current_user)
