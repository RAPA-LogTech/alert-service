import logging

from fastapi import APIRouter, HTTPException

from ..core.slack_client import get_slack_installation_config

logger = logging.getLogger(__name__)
router = APIRouter(tags=["slack"])


@router.get("/channels")
async def get_slack_channels() -> dict:
    """Slack 채널 목록 조회"""
    installation_config = get_slack_installation_config()

    if not installation_config or installation_config.get("status") == "disconnected":
        raise HTTPException(status_code=400, detail="Slack이 아직 연동되지 않았습니다.")

    bot_token = installation_config.get("bot_token")
    if not bot_token:
        raise HTTPException(status_code=400, detail="Slack Bot Token을 찾을 수 없습니다.")

    try:
        import requests

        response = requests.get(
            "https://slack.com/api/conversations.list",
            headers={"Authorization": f"Bearer {bot_token}"},
            params={
                "limit": 100,
                "exclude_archived": "true",
                "types": "public_channel,private_channel",
            },
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("ok"):
            error_msg = data.get("error", "Unknown error")
            if error_msg == "missing_scope":
                raise HTTPException(
                    status_code=400,
                    detail="채널 목록을 불러올 권한이 없습니다. channels:read, groups:read scope이 필요합니다.",
                )
            raise HTTPException(status_code=400, detail=error_msg)

        channels = []
        for ch in data.get("channels", []):
            channels.append(
                {
                    "id": ch.get("id"),
                    "name": ch.get("name"),
                    "isPrivate": ch.get("is_private", False),
                    "isMember": ch.get("is_member", False),
                }
            )

        return {
            "ok": True,
            "channels": channels,
        }

    except Exception as e:
        logger.error(f"Failed to fetch Slack channels: {e}")
        raise HTTPException(status_code=500, detail=f"Slack 채널 목록 조회 실패: {str(e)}")
