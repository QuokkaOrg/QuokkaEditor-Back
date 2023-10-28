from uuid import UUID

from fastapi import HTTPException, Security, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.auth import auth_handler, security
from quokka_editor_back.models.document import Document
from quokka_editor_back.models.user import User


async def get_user_by_token(token: str):
    username = auth_handler.decode_token(token=token)
    try:
        user = await User.get(username=username)
    except DoesNotExist as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials

    user = await get_user_by_token(token=token)

    return user


async def authenticate_websocket(
    document_id: UUID, token: str | None = None
) -> UUID | None:
    try:
        document = await Document.get(id=document_id)
    except DoesNotExist as err:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from err
    if document.shared_by_link:
        return
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    try:
        user = await get_user_by_token(token=token)
    except HTTPException as err:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from err
    return user.id
