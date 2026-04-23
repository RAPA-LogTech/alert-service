import logging
from datetime import datetime

from ..core.config import get_settings
from ..core.slack_client import get_slack_installation_config, save_slack_installation_config

logger = logging.getLogger(__name__)


class SlackMessagingService:
    """Slack 메시지 전송 서비스"""

    def __init__(self):
        self.settings = get_settings()

    def get_installation_info(self) -> dict | None:
        """설치 정보 가져오기"""
        return get_slack_installation_config()

    def get_oauth_config(self) -> dict | None:
        """OAuth 설정 가져오기"""
        from ..core.slack_client import get_slack_oauth_config

        return get_slack_oauth_config()

    def update_channel(self, channel_id: str, channel_name: str) -> bool:
        """채널 변경"""
        try:
            installation = get_slack_installation_config() or {}
            installation.update(
                {
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "updated_at": datetime.utcnow().isoformat(),
                    "status": "active",
                }
            )

            if not save_slack_installation_config(installation):
                return False

            logger.info(f"Channel updated to {channel_id} ({channel_name})")
            return True
        except Exception as e:
            logger.error(f"Failed to update channel: {e}")
            return False

    def delete_installation(self) -> bool:
        """연동 해제"""
        try:
            installation = get_slack_installation_config() or {}
            installation.update(
                {
                    "status": "disconnected",
                    "disconnected_at": datetime.utcnow().isoformat(),
                }
            )

            if not save_slack_installation_config(installation):
                return False

            logger.info("Slack installation deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete installation: {e}")
            return False
