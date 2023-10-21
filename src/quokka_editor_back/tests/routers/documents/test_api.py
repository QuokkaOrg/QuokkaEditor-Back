from time import time_ns

from quokka_editor_back.models.document import Document


async def test_search_document(client, active_user):
    # Given
    await Document.create(
        title=f"First document {time_ns()}",
        content=b"Sample basic content",
        user=active_user,
    )
    await Document.create(
        title=f"Second document {time_ns()}",
        content=b"Sample basic content",
        user=active_user,
    )

    # When
    response = await client.get("/documents/?search_phrase=second")
    json_response = response.json()

    # Then
    assert response.status_code == 200
    assert len(json_response) == 1
    assert "Second document" in json_response[0].get("title")
