from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from tortoise import Tortoise
from tortoise.connection import connections

from quokka_editor_back.routers import auth, documents, users, websockets
from quokka_editor_back.settings import TORTOISE_ORM

MODULE_DIR = Path(__file__).parent.absolute()
templates = Jinja2Templates(directory=MODULE_DIR / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(config=TORTOISE_ORM)
    yield
    await connections.close_all()


app = FastAPI(lifespan=lifespan, debug=True)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/mock-ui")
async def get_mock_ui(request: Request):
    return templates.TemplateResponse("mock-ui.html", {"request": request})


app.include_router(router=websockets.router, prefix="/ws")
app.include_router(router=documents.router, prefix="/documents")
app.include_router(router=auth.router, prefix="/auth")
app.include_router(router=users.router, prefix="/users")
