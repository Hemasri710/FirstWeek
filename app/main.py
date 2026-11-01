from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI

from app import chat, usage
from app.config import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    usage.init()
    yield


app = FastAPI(title="FirstWeek", version="0.1.0", lifespan=lifespan)

app.include_router(chat.router)


@app.get("/")
def root():
    return {"name": "FirstWeek", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health(settings: Annotated[Settings, Depends(get_settings)]):
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/usage")
def get_usage():
    return {"by_model": usage.summary()}