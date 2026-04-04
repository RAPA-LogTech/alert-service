from typing import Any

from pydantic import BaseModel, Field


class IncidentSummary(BaseModel):
    incident_id: str
    alert_name: str | None = None
    severity: str | None = None
    status: str | None = None
    service_info: str | None = None
    created_at: str | None = None
    resolved_at: str | None = None
    slack_ts: str | None = None
    s3_key: str | None = None


class IncidentListResponse(BaseModel):
    items: list[IncidentSummary]
    next_cursor: str | None = None


class IncidentDetailResponse(BaseModel):
    summary: IncidentSummary
    detail: dict[str, Any] = Field(default_factory=dict)
