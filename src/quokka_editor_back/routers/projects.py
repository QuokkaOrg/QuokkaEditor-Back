import os
import uuid
from http.client import HTTPException
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from starlette import status
from tortoise.exceptions import DoesNotExist

from quokka_editor_back.auth.utils import get_current_user
from quokka_editor_back.models.project import Project
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.project import ProjectUpdatePayload

router = APIRouter(tags=["projects"])

MODULE_DIR = Path(__file__).parent.parent.absolute()


def delete_file(file_name: str):
    file_path = str(MODULE_DIR / f"statics/{file_name}")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not found",
        ) from err


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
    project = await get_project(
        project_id=project_id,
        user=current_user,
    )
    if project.images:
        for image_url in project.images:
            file_path = image_url.lstrip("/")
            delete_file(file_path)
    await project.delete()


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


@router.post(
    "/images/{project_id}",
)
async def add_image(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    project = await get_project(
        project_id=project_id,
        user=current_user,
    )
    file_name_without_ext = file.filename.rsplit(".")[0]
    file_name = f"{file_name_without_ext}_{project.title}".replace(" ", "_")
    image_url = str(MODULE_DIR / f"statics/{file_name}")

    with open(image_url, "wb") as buffer:
        buffer.write(await file.read())

    images_list = project.images or []
    images_list.append(file_name)
    project.images = images_list
    await project.save()

    return {"message": "Image uploaded successfully"}


@router.delete("/delete-image/{project_id}")
async def delete_image(
    project_id: uuid.UUID,
    file_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    project = await get_project(
        project_id=project_id,
        user=current_user,
    )
    if project.images and file_name in project.images:
        project.images.remove(file_name)
        await project.save()
        delete_file(file_name)
    else:
        raise HTTPException(status_code=404, detail="Image URL not found in project")

    return {"message": "Image deleted successfully"}


add_pagination(router)
