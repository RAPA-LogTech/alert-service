from fastapi import APIRouter

from ..models.slack import SlackIntegrationResponse, SlackIntegrationStatus
from ..core.slack_client import get_slack_installation_config, get_slack_oauth_config

router = APIRouter(tags=["slack"])


@router.get("/info", response_model=SlackIntegrationResponse)
def get_slack_integration_info() -> SlackIntegrationResponse:
    """현재 Slack 연동 정보 조회"""
    installation_config = get_slack_installation_config() or {}
    oauth_config = get_slack_oauth_config() or {}

    is_connected = bool(
        installation_config.get("channel_id")
        and installation_config.get("status") != "disconnected"
    )
    
    status = SlackIntegrationStatus(
        is_connected=is_connected,
        team_id=installation_config.get("team_id"),
        team_name=installation_config.get("team_name"),
        bot_token="***" if installation_config.get("bot_token") else None,
        installed_channels=installation_config.get("installed_channels"),
        scopes=oauth_config.get("scopes") if oauth_config else None,
    )
    
    message = (
        "Slack이 연동되었습니다." if is_connected 
        else "Slack이 아직 연동되지 않았습니다. /oauth/connect로 연동하세요."
    )
    
    return SlackIntegrationResponse(
        status=status,
        last_updated=installation_config.get("updated_at") or installation_config.get("installed_at"),
        message=message,
    )
