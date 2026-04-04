from fastapi import APIRouter

from .oauth import router as oauth_router
from .events import router as events_router

router = APIRouter(prefix="/v1/slack")

router.include_router(oauth_router, prefix="")
router.include_router(events_router, prefix="")
