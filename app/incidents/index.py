from fastapi import APIRouter

from .query import router as query_router
from .analyze import router as analyze_router
from .detail import router as detail_router

router = APIRouter(prefix="/v1/incidents")

router.include_router(query_router, prefix="")
router.include_router(analyze_router, prefix="")
router.include_router(detail_router, prefix="")
