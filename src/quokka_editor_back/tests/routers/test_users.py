import uuid

import pytest
from fastapi import HTTPException

from quokka_editor_back.routers.users import get_user


async def test_get_user(active_user):
    user = await get_user(active_user.id)

    assert user == active_user


async def test_get_user_does_not_exist():
    with pytest.raises(HTTPException):
        await get_user(uuid.uuid4())
