from time import time_ns

from quokka_editor_back.models.document import Document


async def test_search_document(client):
    # Given
    await Document.create(title=f"First document {time_ns()}", content="Sample basic content")
    await Document.create(title=f"Second document {time_ns()}", content="Sample basic content")

    # When
    response = client.get("/")

    # Then
    assert response.status_code == 200
