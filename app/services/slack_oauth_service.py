from datetime import datetime
import logging
from urllib.parse import urlparse

import requests

from ..core.slack_client import (
    get_slack_installation_config,
    get_slack_oauth_config,
    save_slack_installation_config,
    save_slack_oauth_config,
)

logger = logging.getLogger(__name__)


class SlackOAuthService:
    """Slack OAuth 처리 서비스"""

    def _fetch_team_metadata(self, bot_token: str | None, team_id: str | None = None) -> dict:
        """team.info로 team_domain/team_image를 보강한다."""
        if not bot_token:
            return {}

        team_domain = None

        # team:read 스코프 없이도 auth.test의 url로 도메인 추출 가능
        try:
            auth_test = requests.post(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {bot_token}"},
                timeout=10,
            )
            auth_test.raise_for_status()
            auth_payload = auth_test.json()
            if auth_payload.get("ok") and auth_payload.get("url"):
                host = urlparse(auth_payload["url"]).hostname or ""
                if host.endswith(".slack.com"):
                    team_domain = host.removesuffix(".slack.com")
        except Exception as exc:
            logger.warning("auth.test request failed: %s", exc)

        params = {"team": team_id} if team_id else None
        try:
            response = requests.get(
                "https://slack.com/api/team.info",
                params=params,
                headers={"Authorization": f"Bearer {bot_token}"},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                logger.warning("team.info failed: %s", payload.get("error"))
                return {"team_domain": team_domain}

            team = payload.get("team") or {}
            icon = team.get("icon") or {}
            return {
                "team_domain": team.get("domain") or team_domain,
                "team_image": team.get("image_230") or icon.get("image_132") or icon.get("image_102"),
            }
        except Exception as exc:
            logger.warning("team.info request failed: %s", exc)
            return {"team_domain": team_domain}
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """Slack 인증 URL 생성"""
        oauth_config = get_slack_oauth_config() or {}
        client_id = oauth_config.get("client_id")
        scopes = oauth_config.get("bot_scopes") or "incoming-webhook,chat:write,channels:read"

        if not client_id:
            raise ValueError("Slack Client ID not configured")
        
        return (
            f"https://slack.com/oauth/v2/authorize?"
            f"client_id={client_id}&"
            f"scope={scopes}&"
            f"redirect_uri={redirect_uri}"
        )
    
    def exchange_code_for_token(self, code: str) -> dict | None:
        """인증 코드를 토큰으로 교환"""
        try:
            oauth_config = get_slack_oauth_config() or {}
            client_id = oauth_config.get("client_id")
            client_secret = oauth_config.get("client_secret")

            if not client_id or not client_secret:
                print("Slack OAuth credentials are not configured")
                return None

            response = requests.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                },
                timeout=10,
            )
            response.raise_for_status()
            
            data = response.json()
            if not data.get("ok"):
                print(f"Slack OAuth error: {data.get('error')}")
                return None
            
            return data
        except Exception as e:
            print(f"Failed to exchange code for token: {e}")
            return None
    
    def save_oauth_config(self, oauth_data: dict) -> bool:
        """OAuth 설정을 Secrets Manager에 저장"""
        current_config = get_slack_oauth_config() or {}

        # OAuth 자격 정보는 Secrets Manager 값을 소스로 유지한다.
        client_id = current_config.get("client_id")
        client_secret = current_config.get("client_secret")
        signing_secret = current_config.get("signing_secret")

        if not client_id or not client_secret:
            print("Slack OAuth credentials are missing in Secrets Manager")
            return False

        config = {
            **current_config,
            "client_id": client_id,
            "client_secret": client_secret,
            "signing_secret": signing_secret,
            "team_id": oauth_data.get("team", {}).get("id"),
            "team_name": oauth_data.get("team", {}).get("name"),
            "bot_token": oauth_data.get("access_token"),
            "bot_user_id": oauth_data.get("bot_user_id"),
            "app_id": oauth_data.get("app_id"),
            "scopes": oauth_data.get("scope", "").split(","),
            "bot_scopes": current_config.get("bot_scopes") or oauth_data.get("scope", ""),
            "installed_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

        success = save_slack_oauth_config(config)
        if success:
            print(f"OAuth config saved for team {config['team_id']}")
        else:
            print("Failed to save OAuth config")
        return success
    
    def save_installation(self, oauth_data: dict) -> bool:
        """Slack 설치 정보 저장"""
        current_installation = get_slack_installation_config() or {}
        team_info = oauth_data.get("team", {}) or {}
        bot_token = oauth_data.get("access_token") or current_installation.get("bot_token")
        team_id = team_info.get("id") or current_installation.get("team_id")

        # oauth.v2.access 응답에 domain/icon이 누락되는 경우가 있어 team.info로 보강한다.
        team_meta = self._fetch_team_metadata(bot_token, team_id)
        team_domain = team_info.get("domain") or team_meta.get("team_domain") or current_installation.get("team_domain")
        team_image = (
            team_info.get("image_230")
            or team_info.get("icon", {}).get("image_132")
            or team_info.get("icon", {}).get("image_102")
            or team_meta.get("team_image")
            or current_installation.get("team_image")
        )

        installation = {
            **current_installation,
            "team_id": team_id,
            "team_name": team_info.get("name") or current_installation.get("team_name"),
            "team_domain": team_domain,
            "team_image": team_image,
            "bot_token": bot_token,
            "bot_id": oauth_data.get("bot_user_id"),
            "app_id": oauth_data.get("app_id"),
            "channel_id": oauth_data.get("incoming_webhook", {}).get("channel_id"),
            "channel_name": oauth_data.get("incoming_webhook", {}).get("channel"),
            "installed_channels": [
                {
                    "id": oauth_data.get("incoming_webhook", {}).get("channel_id"),
                    "name": oauth_data.get("incoming_webhook", {}).get("channel"),
                }
            ] if oauth_data.get("incoming_webhook", {}).get("channel_id") else [],
            "webhook_url": oauth_data.get("incoming_webhook", {}).get("url"),
            "installed_by": oauth_data.get("authed_user", {}).get("id"),
            "installed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

        success = save_slack_installation_config(installation)
        if success:
            logger.info(f"Installation info saved for team {installation['team_id']}")
        else:
            print("Failed to save installation info")
        return success
