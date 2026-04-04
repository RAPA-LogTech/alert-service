from fastapi import APIRouter

from ..models.incident import IncidentDetailResponse
from ..services.incident_service import IncidentService

router = APIRouter(prefix="/v1/incidents", tags=["incidents"])
service = IncidentService()


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(incident_id: str) -> IncidentDetailResponse:
    return service.get_incident_detail(incident_id)
