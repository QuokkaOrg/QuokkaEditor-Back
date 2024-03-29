import contextlib
import json
import os
import uuid
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Security, UploadFile
from fastapi.security import HTTPAuthorizationCredentials
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from starlette import status
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from quokka_editor_back.auth import optional_security
from quokka_editor_back.auth.utils import get_current_user
from quokka_editor_back.models.document import Document
from quokka_editor_back.models.project import Project
from quokka_editor_back.models.user import User
from quokka_editor_back.schema.project import (
    ProjectCreatePayload,
    ProjectUpdatePayload,
    ShareInput,
)
from quokka_editor_back.schema.utils import Status

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
            detail="Not found",
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
    search_phrase: str | None = Query(None),
):
    qs = Project.filter(user=current_user)
    if search_phrase:
        qs = qs.filter(Q(title__icontains=search_phrase))

    return await paginate(query=qs.order_by("-id"))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(
    project_payload: ProjectCreatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
):
    document_title = "main"

    async with in_transaction():
        new_project = await Project.create(
            title=project_payload.title,
            user_id=current_user.id,
        )
        await Document.create(
            title=document_title,
            content=json.dumps([""]).encode(),
            user=current_user,
            project=new_project,
        )

    return new_project


def has_access(project: Project, current_user: User | None):
    if project.shared_by_link:
        return True
    if current_user and project.user == current_user:
        return True
    return False


@router.get("/{project_id}")
async def read_project(
    project_id: UUID,
    credentials: HTTPAuthorizationCredentials = Security(optional_security),
):
    project = await get_project(project_id=project_id)
    current_user = None

    if credentials:
        with contextlib.suppress(HTTPException):
            current_user = await get_current_user(credentials)

    if not has_access(project, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return {
        "project": project,
        "documents": await Document.filter(project__id=project_id),
    }


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


@router.post("/share/{project_id}", status_code=status.HTTP_201_CREATED)
async def share_document(
    project_id: UUID,
    payload: ShareInput,
    current_user: Annotated[User, Depends(get_current_user)],
):
    project = await get_project(project_id=project_id)
    project.update_from_dict(payload.dict())
    await project.save()
    return Status(message=f"Shared project {project_id}")


add_pagination(router)
