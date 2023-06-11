from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise, connections

from quokka_editor_back.settings import TORTOISE_ORM
from src.quokka_editor_back.routers import documents, websockets

from fastapi.middleware.cors import CORSMiddleware


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

app.include_router(router=websockets.router, prefix="/ws")
app.include_router(router=documents.router, prefix="/documents")
