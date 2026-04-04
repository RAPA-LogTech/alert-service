import base64
import json
from typing import Any

from fastapi import HTTPException

from ..models.incident import IncidentDetailResponse, IncidentListResponse, IncidentSummary
from ..repositories.incident_repository import IncidentRepository, sanitize_ddb_item


class IncidentService:
    def __init__(self, repository: IncidentRepository | None = None) -> None:
        self._repository = repository or IncidentRepository()

    def list_incidents(self, *, status: str, limit: int, cursor: str | None) -> IncidentListResponse:
        exclusive_start_key = decode_cursor(cursor)
        items, last_evaluated_key = self._repository.query_by_status(
            status=status,
            limit=limit,
            exclusive_start_key=exclusive_start_key,
        )

        summaries = [IncidentSummary.model_validate(sanitize_ddb_item(item)) for item in items]
        return IncidentListResponse(items=summaries, next_cursor=encode_cursor(last_evaluated_key))

    def get_incident_detail(self, incident_id: str) -> IncidentDetailResponse:
        item = self._repository.get_by_id(incident_id)
        if not item:
            raise HTTPException(status_code=404, detail="incident not found")

        summary = IncidentSummary.model_validate(sanitize_ddb_item(item))
        detail = {}
        if summary.s3_key:
            detail = self._repository.get_detail(summary.s3_key)

        return IncidentDetailResponse(summary=summary, detail=detail)


def encode_cursor(last_evaluated_key: dict[str, Any] | None) -> str | None:
    if not last_evaluated_key:
        return None

    encoded = json.dumps(last_evaluated_key, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("utf-8")


def decode_cursor(cursor: str | None) -> dict[str, Any] | None:
    if not cursor:
        return None

    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        data = json.loads(decoded)
        if not isinstance(data, dict):
            raise ValueError("cursor must decode to an object")
        return data
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="invalid cursor") from exc
