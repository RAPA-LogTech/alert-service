from datetime import datetime, timezone

from fastapi import APIRouter

from ..core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.environment,
        "ts": datetime.now(timezone.utc).isoformat(),
        "resources": {
            "ddb_table": settings.ddb_table_slack_messages,
            "ddb_gsi": settings.ddb_gsi_status_created_at,
            "s3_bucket": settings.s3_bucket_slack_messages,
        },
    }
