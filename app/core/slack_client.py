import json
from functools import lru_cache

import boto3

from .config import get_settings


@lru_cache
def get_secrets_manager_client():
    settings = get_settings()
    return boto3.client("secretsmanager", region_name=settings.aws_region)


def _load_secret_json(secret_arn: str | None) -> dict | None:
    if not secret_arn:
        return None

    try:
        client = get_secrets_manager_client()
        response = client.get_secret_value(SecretId=secret_arn)
        secret_string = response.get("SecretString")
        if secret_string:
            return json.loads(secret_string)
    except Exception as e:
        print(f"Failed to retrieve secret {secret_arn}: {e}")
    return None


def _save_secret_json(secret_arn: str | None, payload: dict) -> bool:
    if not secret_arn:
        return False

    try:
        client = get_secrets_manager_client()
        client.put_secret_value(
            SecretId=secret_arn, SecretString=json.dumps(payload, ensure_ascii=False)
        )
        return True
    except Exception as e:
        print(f"Failed to store secret {secret_arn}: {e}")
        return False


def get_slack_oauth_config() -> dict | None:
    """AWS Secrets Manager에서 Slack OAuth 설정 가져오기"""
    settings = get_settings()
    return _load_secret_json(settings.slack_oauth_config_secret_arn)


def get_slack_installation_config() -> dict | None:
    """AWS Secrets Manager에서 Slack 설치 정보 가져오기"""
    settings = get_settings()
    return _load_secret_json(settings.slack_installation_secret_arn)


def save_slack_oauth_config(payload: dict) -> bool:
    """Slack OAuth 설정을 Secrets Manager에 저장"""
    settings = get_settings()
    return _save_secret_json(settings.slack_oauth_config_secret_arn, payload)


def save_slack_installation_config(payload: dict) -> bool:
    """Slack 설치 정보를 Secrets Manager에 저장"""
    settings = get_settings()
    return _save_secret_json(settings.slack_installation_secret_arn, payload)
