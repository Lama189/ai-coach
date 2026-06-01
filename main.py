import logging

import app.infrastructure.postgres.models
from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.exercises import router as exercises_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="AI Coach API"
)


@app.get("/")
async def root():
    return {
        "message": "AI Coach API is running",
        "docs": "/docs",
        "health": "/health",
    }

app.include_router(users_router)
app.include_router(exercises_router)