from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from tortoise.contrib.fastapi import register_tortoise

from quokka_editor_back.routers import (
    auth,
    document_templates,
    documents,
    users,
    websockets,
    # projects,
)
from quokka_editor_back.settings import TORTOISE_ORM

MODULE_DIR = Path(__file__).parent.absolute()
templates = Jinja2Templates(directory=MODULE_DIR / "templates")


app = FastAPI(debug=True)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/mock-ui/{document_id}")
async def get_mock_ui(request: Request, document_id: str):
    return templates.TemplateResponse(
        "mock-ui.html", {"request": request, "document_id": document_id}
    )


app.include_router(router=websockets.router, prefix="/ws")
app.include_router(router=documents.router, prefix="/documents")
app.include_router(router=document_templates.router, prefix="/templates")
app.include_router(router=auth.router, prefix="/auth")
app.include_router(router=users.router, prefix="/users")
# app.include_router(router=projects.router, prefix="/projects")

# register_tortoise(
#     app,
#     config=TORTOISE_ORM,
#     generate_schemas=True,
#     add_exception_handlers=True,
# )
