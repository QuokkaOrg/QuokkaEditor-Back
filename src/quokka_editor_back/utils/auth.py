from datetime import datetime, timedelta

from fastapi import HTTPException
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import SecretStr
from starlette import status

from quokka_editor_back.settings import settings


class Auth:
    hasher = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret = settings.secret_key

    def encode_password(self, password: SecretStr):
        return self.hasher.hash(password.get_secret_value())

    def verify_password(self, password: str, encoded_password: str):
        return self.hasher.verify(password, encoded_password)

    def encode_token(self, username):
        payload = {
            "exp": datetime.utcnow()
            + timedelta(minutes=settings.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "sub": username,
        }
        return jwt.encode(payload, self.secret, algorithm=settings.algorithm)

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=[settings.algorithm])
            return payload["sub"]
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    def refresh_token(self, expired_token):
        try:
            payload = jwt.decode(
                expired_token,
                self.secret,
                algorithms=[settings.algorithm],
                options={"verify_exp": False},
            )
            username = payload["sub"]
            new_token = self.encode_token(username)
            return {"token": new_token}
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
