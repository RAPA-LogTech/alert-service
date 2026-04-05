from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime
from urllib.parse import urlparse

from ..core.slack_client import get_slack_installation_config, get_slack_oauth_config

logger = logging.getLogger(__name__)
router = APIRouter(tags=["slack"])


class UpdateChannelPayload(BaseModel):
    channel_id: str
    channel_name: str | None = None
    send_test_message: bool = False


@router.get("/status")
async def get_slack_status() -> dict:
    """Slack 연동 상태 조회"""
    installation_config = get_slack_installation_config() or {}
    oauth_config = get_slack_oauth_config() or {}

    team_domain = installation_config.get("team_domain")
    team_image = installation_config.get("team_image")
    bot_token = installation_config.get("bot_token")
    team_id = installation_config.get("team_id")

    # 과거 설치 데이터에 team_domain이 비어 있는 경우 team.info로 보강
    if (not team_domain or not team_image) and bot_token:
        try:
            import requests

            # team:read 없이도 auth.test URL에서 workspace 도메인을 추출할 수 있음
            if not team_domain:
                auth_resp = requests.post(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {bot_token}"},
                    timeout=10,
                )
                auth_resp.raise_for_status()
                auth_payload = auth_resp.json()
                if auth_payload.get("ok") and auth_payload.get("url"):
                    host = urlparse(auth_payload["url"]).hostname or ""
                    if host.endswith(".slack.com"):
                        team_domain = host.removesuffix(".slack.com")

            params = {"team": team_id} if team_id else None
            response = requests.get(
                "https://slack.com/api/team.info",
                params=params,
                headers={"Authorization": f"Bearer {bot_token}"},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("ok"):
                team = payload.get("team") or {}
                icon = team.get("icon") or {}
                team_domain = team_domain or team.get("domain")
                team_image = team_image or team.get("image_230") or icon.get("image_132") or icon.get("image_102")
        except Exception as exc:
            logger.warning("Slack team.info fallback failed: %s", exc)
    
    is_connected = bool(
        installation_config.get("channel_id")
        and installation_config.get("status") != "disconnected"
    )
    
    return {
        "ok": True,
        "isConnected": is_connected,
        "teamId": installation_config.get("team_id"),
        "teamName": installation_config.get("team_name"),
        "teamDomain": team_domain,
        "teamImage": team_image,
        "channelId": installation_config.get("channel_id"),
        "channelName": installation_config.get("channel_name"),
        "installedAt": installation_config.get("updated_at") or installation_config.get("installed_at"),
        "scopes": oauth_config.get("scopes") or [],
    }


@router.delete("/status")
async def disconnect_slack() -> dict:
    """Slack 연동 해제"""
    from ..services.slack_messaging_service import SlackMessagingService

    msg_service = SlackMessagingService()
    
    # 설치 정보를 먼저 가져오기 (해제 전 알림 전송용)
    installation_info = msg_service.get_installation_info()
    
    if not installation_info or installation_info.get("status") == "disconnected":
        return {
            "ok": True,
            "message": "Slack이 이미 연동되지 않았습니다.",
            "disconnectedAt": None,
        }
    
    # 해제 전 알림 메시지 전송 시도
    notice_sent = False
    try:
        import requests
        
        bot_token = installation_info.get("bot_token")
        channel_id = installation_info.get("channel_id")
        
        if bot_token and channel_id:
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {bot_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "channel": channel_id,
                    "text": "ℹ️ LogTech Slack 연동이 해제됩니다. 이후 이 채널로 알림이 전송되지 않습니다.",
                },
                timeout=10,
            )
            notice_sent = response.ok
    except Exception as e:
        logger.warning(f"Failed to send disconnect notice: {e}")
    
    # 연동 정보 삭제
    success = msg_service.delete_installation()
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Slack 연동 해제 중 오류가 발생했습니다."
        )
    
    return {
        "ok": True,
        "disconnectedAt": datetime.utcnow().isoformat(),
        "noticeSent": notice_sent,
    }


@router.patch("/config")
async def update_slack_config(payload: UpdateChannelPayload) -> dict:
    """Slack 채널 설정 변경"""
    from ..services.slack_messaging_service import SlackMessagingService

    msg_service = SlackMessagingService()
    
    installation_info = msg_service.get_installation_info()
    
    if not installation_info or installation_info.get("status") == "disconnected":
        raise HTTPException(
            status_code=400,
            detail="Slack이 아직 연동되지 않았습니다."
        )
    
    # 채널 변경
    channel_name = payload.channel_name or payload.channel_id
    success = msg_service.update_channel(payload.channel_id, channel_name)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="채널 변경 중 오류가 발생했습니다."
        )
    
    # 테스트 메시지 전송 요청 시
    if payload.send_test_message:
        try:
            import requests
            
            bot_token = installation_info.get("bot_token")
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {bot_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "channel": payload.channel_id,
                    "text": "[TEST] 채널이 변경되었습니다. LogTech 알림이 이어서 전송됩니다.",
                },
                timeout=10,
            )
            if not response.ok:
                logger.warning(f"Failed to send test message after channel change: {response.text}")
        except Exception as e:
            logger.warning(f"Failed to send test message: {e}")
    
    return {
        "ok": True,
        "message": f"채널이 {channel_name}(으)로 변경되었습니다.",
        "channelId": payload.channel_id,
        "channelName": channel_name,
        "updatedAt": datetime.utcnow().isoformat(),
    }
