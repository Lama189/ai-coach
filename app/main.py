import logging
import app.infrastructure.postgres.models
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.application.dependencies import get_embedding_service
from app.infrastructure.storage.client import get_minio_client
from app.infrastructure.storage.bucket_initializer import ensure_bucket_exists

from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.exercises import router as exercises_router
from app.api.v1.routes.programs import router as programs_router
from app.api.v1.routes.insights import router as insights_router
from app.api.v1.routes.knowledge import router as knowledge_router

from app.api.v1.middlewares.req_id import RequestIDMiddleware


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_embedding_service()

    minio_client = get_minio_client()
    ensure_bucket_exists(minio_client, settings.minio_bucket)

    logger.info(
        "MinIO bucket ensured",
        extra={"bucket": settings.minio_bucket},
    )

    client = aioredis.from_url(settings.redis_url)
    try:
        await client.ping()
        logger.info("Redis подключён успешно")
    except Exception as e:
        raise RuntimeError(f"Redis недоступен: {e}")
    finally:
        await client.aclose()

    setup_logging()

    yield


app = FastAPI(
    title="AI Coach API",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
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
app.include_router(knowledge_router)


@app.exception_handler(ValueError)
async def value_error_exception_handler(req: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )