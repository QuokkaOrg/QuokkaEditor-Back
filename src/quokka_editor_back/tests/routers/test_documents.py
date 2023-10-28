from fastapi.testclient import TestClient

from quokka_editor_back.models.document import ShareRole
from quokka_editor_back.schema.document import ShareInput


async def test_share_document(
    client: TestClient,
    document,
    mock_get_current_user,
):
    # Given
    document.shared_by_link = False
    document.shared_role = ShareRole.COMMENT
    await document.save()
    payload = ShareInput(shared_role=ShareRole.EDIT, shared_by_link=True)

    # When
    result = client.post(f"documents/share/{document.id}", json=payload.dict())

    # Then
    result_json = result.json()
    assert result.status_code == 200
    assert result_json == {"message": f"Shared document {document.id}"}
    await document.refresh_from_db()
    assert document.shared_role == ShareRole.EDIT
    assert document.shared_by_link


async def test_share_document_unauthorized_user(
    client: TestClient,
    document,
):
    # Given
    payload = ShareInput(shared_role=ShareRole.EDIT, shared_by_link=True)

    # When
    result = client.post(f"documents/share/{document.id}", json=payload.dict())

    # Then
    assert result.status_code == 403


async def test_share_document_no_document(
    client: TestClient,
    mock_get_current_user,
):
    # Given
    payload = ShareInput(shared_role=ShareRole.EDIT, shared_by_link=True)

    # When
    result = client.post("documents/share/test-id", json=payload.dict())

    # Then
    assert result.status_code == 422
