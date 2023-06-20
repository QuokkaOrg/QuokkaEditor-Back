from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, SecretStr
from starlette import status
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.models.user import User
from quokka_editor_back.settings import settings


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserSchema(BaseModel):
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None


class CreateUser(BaseModel):
    email: EmailStr
    password: SecretStr


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
router = APIRouter(tags=["auth"])


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(username: str, password: str) -> User | bool:
    try:
        user = await User.get(email=username)
    except DoesNotExist:
        return False

    if not verify_password(password, user.hashed_password):
        return False
    return user


async def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if not (username := payload.get("sub")):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    try:
        user = await User.get(email=username)
    except DoesNotExist:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


@router.post("/token")
async def login_for_access_token(
    payload: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await authenticate_user(username=payload.username, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = await create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: Annotated[CreateUser, Depends()]):
    if await User.get_or_none(email=payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )
    await User.create(
        email=payload.email,
        hashed_password=pwd_context.hash(payload.password.get_secret_value()),
        is_active=True,
    )
