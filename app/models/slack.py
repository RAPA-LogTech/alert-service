from pydantic import BaseModel, Field


class SlackIntegrationStatus(BaseModel):
    """Slack 연동 상태"""
    is_connected: bool = Field(default=False, description="Slack이 연동되었는지 여부")
    team_id: str | None = Field(default=None, description="Slack Workspace ID")
    team_name: str | None = Field(default=None, description="Slack Workspace 이름")
    bot_token: str | None = Field(default=None, description="Bot Token (마스킹)")
    installed_channels: list[dict] | None = Field(
        default=None, description="설치된 채널 목록"
    )
    scopes: list[str] | None = Field(default=None, description="Bot Scopes")


class SlackIntegrationResponse(BaseModel):
    """Slack 연동 정보 응답"""
    status: SlackIntegrationStatus
    last_updated: str | None = None
    message: str = ""
