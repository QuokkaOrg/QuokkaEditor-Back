from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
