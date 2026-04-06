from fastapi import APIRouter
from pydantic import BaseModel, Field
import logging

from ..core.slack_client import get_slack_installation_config, save_slack_installation_config

logger = logging.getLogger(__name__)
router = APIRouter(tags=["slack"])

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]


class AlertSettings(BaseModel):
    renotify_interval_minutes: int = Field(default=60, ge=1, le=1440)
    min_severity: str = Field(default="medium")
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = Field(default="02:00")  # HH:MM
    quiet_hours_end: str = Field(default="07:00")    # HH:MM
    quiet_hours_critical_only: bool = True
    include_service_info: bool = True
    include_trace_link: bool = True
    include_log_link: bool = True


DEFAULT_SETTINGS = AlertSettings()


def _get_alert_settings(installation: dict) -> AlertSettings:
    raw = installation.get("alert_settings") or {}
    try:
        return AlertSettings.model_validate(raw)
    except Exception:
        return DEFAULT_SETTINGS


@router.get("/alert-settings")
async def get_alert_settings() -> dict:
    installation = get_slack_installation_config() or {}
    settings = _get_alert_settings(installation)
    return {"ok": True, "settings": settings.model_dump()}


@router.put("/alert-settings")
async def update_alert_settings(payload: AlertSettings) -> dict:
    installation = get_slack_installation_config() or {}

    if payload.min_severity not in SEVERITY_LEVELS:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"min_severity must be one of {SEVERITY_LEVELS}")

    installation["alert_settings"] = payload.model_dump()

    if not save_slack_installation_config(installation):
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="알람 설정 저장에 실패했습니다.")

    logger.info("Alert settings updated")
    return {"ok": True, "settings": payload.model_dump()}
