from fastapi import APIRouter

from .oauth import router as oauth_router
from .events import router as events_router
from .info import router as info_router
from .channels import router as channels_router
from .test import router as test_router
from .status import router as status_router

router = APIRouter(prefix="/v1/slack")

router.include_router(oauth_router, prefix="")
router.include_router(events_router, prefix="")
router.include_router(info_router, prefix="")
router.include_router(channels_router, prefix="")
router.include_router(test_router, prefix="")
router.include_router(status_router, prefix="")

