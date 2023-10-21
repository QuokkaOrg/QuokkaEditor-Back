from fastapi.testclient import TestClient
import httpx
from quokka_editor_back.app import app as asgi_app

import pytest
from pydantic import PostgresDsn
from tortoise import Tortoise
from tortoise.backends.base.config_generator import generate_config
from tortoise.contrib.test import _init_db

from quokka_editor_back.models.document import Document
from quokka_editor_back.models.user import User
from quokka_editor_back.settings import TORTOISE_ORM, settings

TORTOISE_TEST_DB = PostgresDsn.build(
    scheme=settings.database_dsn.scheme,
    user=settings.database_dsn.user,
    password=settings.database_dsn.password,
    host=settings.database_dsn.host,
    tld=settings.database_dsn.tld,
    host_type=settings.database_dsn.host_type,
    port=settings.database_dsn.port,
    path=f"{settings.database_dsn.path}_TEST_{{}}",
    query=settings.database_dsn.query,
    fragment=settings.database_dsn.fragment,
)


@pytest.fixture(autouse=True)
async def initialize_tests():
    await _init_db(
        generate_config(
            TORTOISE_TEST_DB,
            app_modules={
                "quokka_editor_back": TORTOISE_ORM["apps"]["quokka_editor_back"][
                    "models"
                ]
            },
            testing=True,
            connection_label="quokka_editor_back",
        ),
    )
    yield
    await Tortoise._drop_databases()


@pytest.fixture
async def fastapi_app():
    return asgi_app


@pytest.fixture
async def client(fastapi_app):
    async with httpx.AsyncClient(
        app=fastapi_app, base_url="http://localhost:8100"
    ) as test_client:
        yield test_client


@pytest.fixture
async def active_user() -> User:
    return await User.create(
        username="test_user",
        email="test@test.com",
        first_name="tester",
        last_name="test",
        hashed_password="",
        is_active=True,
    )


@pytest.fixture
async def mocked_document(active_user) -> Document:
    return await Document.create(
        title="Sample title 1",
        content=b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut",
        user=active_user,
    )
