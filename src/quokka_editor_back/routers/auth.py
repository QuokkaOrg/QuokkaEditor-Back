from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from starlette import status

from quokka_editor_back.auth import auth_handler, security
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.auth import UserCreate, UserLogin

router = APIRouter(tags=["auth"])


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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username")
    if not auth_handler.verify_password(
        password=payload.password.get_secret_value(),
        encoded_password=user.hashed_password,
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    token = auth_handler.encode_token(user.username)
    return {"token": token}


@router.get("/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    expired_token = credentials.credentials
    return auth_handler.refresh_token(expired_token)
