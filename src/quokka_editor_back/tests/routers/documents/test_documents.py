import uuid

import pytest

from fastapi import HTTPException

from quokka_editor_back.routers.documents import get_document


async def test_get_document(mocked_document):
    document = await get_document(mocked_document.id)
    assert mocked_document == document


async def test_get_document_does_not_exist():
    with pytest.raises(HTTPException):
        await get_document(uuid.uuid4())
