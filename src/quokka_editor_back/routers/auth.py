from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, SecretStr
from starlette import status
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.utils.auth import Auth
from quokka_editor_back.models.user import User


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: SecretStr


class UserLogin(BaseModel):
    username: str
    password: SecretStr


security = HTTPBearer()
auth_handler = Auth()

router = APIRouter(tags=["auth"])


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


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: UserCreate):
    user = await User.get_or_none(username=payload.username)
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )

    await User.create(
        username=payload.username,
        email=payload.email,
        hashed_password=auth_handler.encode_password(payload.password),
        is_active=True,
    )


@router.post("/login")
async def login(payload: UserLogin):
    user = await User.get_or_none(username=payload.username)
    if user is None:
        return HTTPException(status_code=401, detail="Invalid username")
    if not auth_handler.verify_password(
        password=payload.password.get_secret_value(),
        encoded_password=user.hashed_password,
    ):
        return HTTPException(status_code=401, detail="Invalid password")
    token = auth_handler.encode_token(user.username)
    return {"token": token}


@router.get("/refresh")
def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    expired_token = credentials.credentials
    return auth_handler.refresh_token(expired_token)
