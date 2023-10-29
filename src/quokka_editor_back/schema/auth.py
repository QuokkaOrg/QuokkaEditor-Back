from pydantic import BaseModel, EmailStr, SecretStr


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
