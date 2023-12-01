from http.client import HTTPException
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from starlette import status
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.auth.utils import get_current_user
from quokka_editor_back.models.project import Project
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.project import ProjectUpdatePayload

router = APIRouter(tags=["projects"])


async def get_project(
    project_id: UUID,
    user: User | None = None,
) -> Project:
    filters: dict[str, Any] = {"id": project_id}
    if user:
        filters["user"] = user
    try:
        return await Project.get(**filters).prefetch_related("user")
    except DoesNotExist as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        ) from err


@router.get("/", response_model=Page)
async def read_all(
    current_user: Annotated[User, Depends(get_current_user)],
):
    qs = Project.filter(user=current_user)

    return await paginate(query=qs.order_by("-id"))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(
    current_user: Annotated[User, Depends(get_current_user)],
):
    title = "Draft Project"

    new_project = await Project.create(
        title=title,
        user_id=current_user.id,
    )
    return new_project


@router.get("/{project_id}")
async def read_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_project(project_id=project_id, user=current_user)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    is_deleted = await Project.filter(id=project_id, user=current_user).delete()
    if not is_deleted:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")


@router.patch(
    "/{project_id}",
)
async def update_project(
    project_id: UUID,
    project_payload: ProjectUpdatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
):
    project = await get_project(
        project_id=project_id,
        user=current_user,
    )
    if project_payload.title:
        project.title = project_payload.title
    await project.save()
    return project


add_pagination(router)
