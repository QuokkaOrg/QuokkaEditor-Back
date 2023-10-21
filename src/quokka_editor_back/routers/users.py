from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.models.user import User
from quokka_editor_back.auth.auth import get_current_user
from quokka_editor_back.schema.user import UserSchema

router = APIRouter(tags=["users"])


async def get_user(user_id: UUID) -> User:
    try:
        return await User.get(id=user_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {user_id} not found",
        )


@router.get(
    "/me",
    response_model=UserSchema,
    responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}},
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_user(user_id=current_user.id)


@router.patch(
    "/me",
    response_model=UserSchema,
    responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}},
)
async def update_user(
    user_payload: UserSchema,
    current_user: Annotated[User, Depends(get_current_user)],
):
    user = await get_user(user_id=current_user.id)
    user.update_from_dict(
        {
            "username": user_payload.username,
            "email": user_payload.email,
            "first_name": user_payload.first_name,
            "last_name": user_payload.last_name,
            "is_active": user_payload.is_active,
        }
    )
