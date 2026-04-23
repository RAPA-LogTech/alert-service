import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from ..core.slack_client import get_slack_oauth_config
from ..services.slack_oauth_service import SlackOAuthService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["slack"])


@router.get("/oauth/ready")
async def get_oauth_ready() -> dict:
    """Slack OAuth 시작 가능 여부 확인"""
    oauth_config = get_slack_oauth_config() or {}
    client_id = oauth_config.get("client_id")
    client_secret = oauth_config.get("client_secret")

    ready = bool(client_id and client_secret)
    return {
        "ok": True,
        "ready": ready,
        "message": "Slack OAuth 준비 완료"
        if ready
        else "Slack OAuth 설정(client_id/client_secret)이 없습니다.",
    }


@router.get("/oauth/connect")
async def slack_connect(
    redirect_uri: str = Query(None, description="OAuth 콜백 URI"),
) -> RedirectResponse:
    """Slack OAuth 인증 시작"""
    service = SlackOAuthService()
    oauth_config = get_slack_oauth_config() or {}

    if not oauth_config.get("client_id"):
        raise HTTPException(status_code=400, detail="Slack Client ID not configured")

    auth_url = service.get_authorization_url(redirect_uri or "")
    return RedirectResponse(url=auth_url)


@router.get("/oauth/callback")
async def slack_callback(
    code: str = Query(..., description="Slack authorization code"),
    _state: str | None = Query(None, alias="state", description="OAuth state"),
) -> dict:
    """Slack OAuth 콜백 처리"""
    service = SlackOAuthService()
    oauth_config = get_slack_oauth_config() or {}

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    if not oauth_config.get("client_id") or not oauth_config.get("client_secret"):
        raise HTTPException(status_code=500, detail="Slack credentials not configured")

    # 코드를 토큰으로 교환
    oauth_data = service.exchange_code_for_token(code)
    if not oauth_data:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    # DynamoDB에 OAuth 설정 저장
    if not service.save_oauth_config(oauth_data):
        raise HTTPException(status_code=500, detail="Failed to save OAuth configuration")

    # 설치 정보 저장
    if not service.save_installation(oauth_data):
        raise HTTPException(status_code=500, detail="Failed to save installation info")

    return {
        "success": True,
        "message": f"Slack 연동 완료! Team: {oauth_data.get('team', {}).get('name')}",
        "teamId": oauth_data.get("team", {}).get("id"),
        "teamName": oauth_data.get("team", {}).get("name"),
        "botId": oauth_data.get("bot_user_id"),
    }
