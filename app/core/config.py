from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "alert-service"
    environment: str = "local"
    aws_region: str = "ap-northeast-2"

    ddb_table_slack_messages: str = "log-platform-dev-slack-messages"
    ddb_gsi_status_created_at: str = "status-created_at-index"
    s3_bucket_slack_messages: str = ""

    slack_client_id: str | None = None
    slack_client_secret: str | None = None
    slack_signing_secret: str | None = None
    slack_bot_token: str | None = None
    slack_bot_scopes: str | None = None
    slack_oauth_config_secret_arn: str | None = None
    slack_installation_secret_arn: str | None = None

    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parents[2] / ".env"),
            str(Path(__file__).resolve().parents[2] / ".env.example"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
