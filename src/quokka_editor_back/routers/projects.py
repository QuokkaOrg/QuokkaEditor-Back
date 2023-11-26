# from http.client import HTTPException
# from typing import Any, Annotated
# from uuid import UUID
#
# from fastapi import APIRouter, Depends, Query
# from fastapi_pagination import Page, add_pagination
# from fastapi_pagination.ext.tortoise import paginate
# from starlette import status
# from tortoise.exceptions import DoesNotExist
#
# from quokka_editor_back.auth.utils import get_current_user
# from quokka_editor_back.models.projects import Project
# from quokka_editor_back.models.user import User
#
# router = APIRouter(tags=["projects"])
#
#
# async def get_project(
#     document_id: UUID,
#     user: User | None = None,
# ) -> Project:
#     filters: dict[str, Any] = {"id": document_id}
#     if user:
#         filters["user"] = user
#     try:
#         document = await Project.get(**filters).prefetch_related("user")
#         return document
#     except DoesNotExist as err:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Document {document_id} not found",
#         ) from err
#
#
# @router.get("/", response_model=Page)
# async def read_all(
#     current_user: Annotated[User, Depends(get_current_user)],
# ):
#     qs = Project.filter(user=current_user)
#
#     return await paginate(query=qs.order_by("-id"))
#
#
# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def create_document(
#     current_user: Annotated[User, Depends(get_current_user)],
#     template_id: UUID | None = None,
# ):
#     title = "Draft Project"
#     content = json.dumps([""]).encode()
#
#     if template_id:
#         try:
#             document_template = await ProjectTemplate.get(id=template_id)
#         except DoesNotExist as err:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Project Template {template_id} not found",
#             ) from err
#         title = document_template.title
#         content = document_template.content
#
#     new_document = await Project.create(
#         title=title,
#         user_id=current_user.id,
#         content=content,
#     )
#     return new_document
#
#
# def has_access(document: Project, current_user: User | None):
#     if document.shared_by_link:
#         return True
#     if current_user and document.user == current_user:
#         return True
#     return False
#
#
# @router.get("/{document_id}")
# async def read_document(
#     document_id: UUID,
#     credentials: HTTPAuthorizationCredentials = Security(optional_security),
# ):
#     document = await get_document(document_id=document_id)
#     current_user = None
#
#     if credentials:
#         with contextlib.suppress(HTTPException):
#             current_user = await get_current_user(credentials)
#
#     if not has_access(document, current_user):
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Project {document_id} not found",
#         )
#
#     return document
#
#
# @router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_document(
#     document_id: UUID,
#     current_user: Annotated[User, Depends(get_current_user)],
# ):
#     is_deleted = await Project.filter(id=document_id, user=current_user).delete()
#     if not is_deleted:
#         raise HTTPException(status_code=404, detail=f"Project {document_id} not found")
#
#
# @router.patch(
#     "/{document_id}",
# )
# async def update_document(
#     document_id: UUID,
#     document_payload: ProjectUpdatePayload,
#     current_user: Annotated[User, Depends(get_current_user)],
# ):
#     document = await get_document(document_id=document_id)
#     if document_payload.title:
#         document.title = document_payload.title
#     if document_payload.content:
#         document.content = json.dumps(document_payload.content).encode()
#     await document.save()
#     return document
#
#
# add_pagination(router)
