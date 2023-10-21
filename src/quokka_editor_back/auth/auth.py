from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from quokka_editor_back.models.user import User
from quokka_editor_back.auth.old_auth import Auth
import jwt
from quokka_editor_back.settings import settings
from tortoise.exceptions import DoesNotExist

security = HTTPBearer()
auth_handler = Auth()


def create_access_token(data: dict):
    encoded_jwt = jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials

    username = auth_handler.decode_token(token=token)
    try:
        user = await User.get(username=username)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user
