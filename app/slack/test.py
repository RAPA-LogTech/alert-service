import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.slack_client import get_slack_installation_config

logger = logging.getLogger(__name__)
router = APIRouter(tags=["slack"])


class TestMessagePayload(BaseModel):
    text: str | None = None


@router.post("/test")
async def send_test_message(payload: TestMessagePayload) -> dict:
    """테스트 메시지 전송"""
    installation_config = get_slack_installation_config()

    if not installation_config or installation_config.get("status") == "disconnected":
        raise HTTPException(status_code=400, detail="Slack이 아직 연동되지 않았습니다.")

    bot_token = installation_config.get("bot_token")
    channel_id = installation_config.get("channel_id")
    channel_name = installation_config.get("channel_name", "unknown")

    if not bot_token or not channel_id:
        raise HTTPException(status_code=400, detail="Slack 채널 정보가 없습니다.")

    text = payload.text or "[TEST] LogTech Alert Pipeline Health Check"

    try:
        import requests

        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "channel": channel_id,
                "text": text,
            },
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("ok"):
            raise HTTPException(
                status_code=400,
                detail=f"Slack 메시지 전송 실패: {data.get('error', 'Unknown error')}",
            )

        return {
            "ok": True,
            "channel": channel_name,
            "sentAt": __import__("datetime").datetime.utcnow().isoformat(),
            "message": "테스트 메시지가 전송되었습니다.",
        }

    except Exception as e:
        logger.error(f"Failed to send test message: {e}")
        raise HTTPException(status_code=500, detail=f"테스트 메시지 전송 실패: {str(e)}")
