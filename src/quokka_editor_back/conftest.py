from fastapi.testclient import TestClient
from quokka_editor_back.app import app

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
def client():
    client = TestClient(app)
    yield client


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
async def document() -> Document:
    return await Document.create(
        title=f"Sample title 1",
        content="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut",
        # labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
        # aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum
        # dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
        # deserunt mollit anim id est laborum."""
    )
