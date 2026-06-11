import logging
import app.infrastructure.postgres.models
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from redis import asyncio as aioredis

from app.core.config import get_settings
from app.application.dependencies import get_embedding_service

from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.exercises import router as exercises_router
from app.api.v1.routes.programs import router as programs_router
from app.api.v1.routes.insights import router as insights_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_embedding_service()

    client = aioredis.from_url(settings.redis_url)
    try:
        await client.ping()
        logger.info("Redis подключён успешно")
    except Exception as e:
        raise RuntimeError(f"Redis недоступен: {e}")
    finally:
        await client.aclose()

    yield


app = FastAPI(
    title="AI Coach API",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {
        "message": "AI Coach API is running",
        "docs": "/docs",
        "health": "/health",
    }


app.include_router(users_router)
app.include_router(exercises_router)
app.include_router(programs_router)
app.include_router(insights_router)


@app.exception_handler(ValueError)
async def value_error_exception_handler(req: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )