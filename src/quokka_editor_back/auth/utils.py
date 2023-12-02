import contextlib
import logging
from uuid import UUID

from fastapi import HTTPException, Security, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.auth import auth_handler, security
from quokka_editor_back.models.document import Document, ShareRole
from quokka_editor_back.models.user import User

logger = logging.getLogger(__name__)


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
) -> tuple[User | None, ShareRole | None]:
    user = None
    try:
        document = await Document.get(id=document_id)
    except DoesNotExist as err:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from err
    if token:
        with contextlib.suppress(HTTPException):
            user = await get_user_by_token(token=token)
    if user:
        return user, None
    if document.shared_by_link:
        return None, document.shared_role
    raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
