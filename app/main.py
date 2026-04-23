import logging

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .core.config import get_settings
from .incidents.index import router as incidents_router
from .slack.index import router as slack_router

logger = logging.getLogger("uvicorn.error")

router = APIRouter()


@router.get("/")
async def root():
    return {"status": "ok"}


def create_app() -> FastAPI:
    settings = get_settings()

    fastapi_app = FastAPI(title=settings.service_name, version="0.1.0")

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @fastapi_app.middleware("http")
    async def log_request_url(request: Request, call_next):
        logger.info("Incoming request: %s %s", request.method, request.url)
        return await call_next(request)

    fastapi_app.include_router(health_router)
    fastapi_app.include_router(router)
    fastapi_app.include_router(incidents_router)
    fastapi_app.include_router(slack_router)

    return fastapi_app


app = create_app()
