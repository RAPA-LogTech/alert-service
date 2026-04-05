from fastapi import APIRouter, Query

from ..models.incident import IncidentListResponse
from ..services.incident_service import IncidentService

router = APIRouter(tags=["incidents"])
service = IncidentService()


@router.get("/", response_model=IncidentListResponse)
def list_incidents(
    status: str = Query(pattern="^(ongoing|analyzed|resolved)$"),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = Query(default=None),
) -> IncidentListResponse:
    return service.list_incidents(status=status, limit=limit, cursor=cursor)
