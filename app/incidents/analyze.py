import json
import logging
import os

import boto3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["incidents"])

LAMBDA_AGENT_ARN = os.environ.get("LAMBDA_AGENT_ARN", "")


class AnalyzeRequest(BaseModel):
    incident_id: str


@router.post("/analyze")
async def request_analysis(payload: AnalyzeRequest) -> dict:
    """대시보드에서 분석 요청 트리거"""
    from ..core.config import get_settings
    from ..repositories.incident_repository import IncidentRepository, sanitize_ddb_item

    if not LAMBDA_AGENT_ARN:
        raise HTTPException(status_code=500, detail="Lambda Agent ARN이 설정되지 않았습니다.")

    settings = get_settings()
    repo = IncidentRepository()

    item = repo.get_by_id(payload.incident_id)
    if not item:
        raise HTTPException(status_code=404, detail="incident not found")

    clean = sanitize_ddb_item(item)
    alert_name = clean.get("alert_name", "")
    slack_ts = clean.get("slack_ts", "")
    slack_channel = clean.get("slack_channel", "")
    severity = clean.get("severity", "high")

    if clean.get("status") != "ongoing":
        raise HTTPException(status_code=400, detail="이미 분석되었거나 해결된 인시던트입니다.")

    # S3에서 question 추가 조회 (분석 품질 향상)
    question = alert_name
    s3_key = clean.get("s3_key", "")
    if s3_key:
        try:
            s3_detail = repo.get_detail(s3_key)
            question = s3_detail.get("question") or alert_name
        except Exception:
            pass

    try:
        client = boto3.client("lambda", region_name=settings.aws_region)
        client.invoke(
            FunctionName=LAMBDA_AGENT_ARN,
            InvocationType="Event",  # 비동기
            Payload=json.dumps(
                {
                    "_action": "run_analysis",
                    "alert_name": alert_name,
                    "slack_ts": slack_ts,
                    "slack_channel": slack_channel,
                    "severity": severity,
                    "question": question,
                }
            ).encode(),
        )
    except Exception as e:
        logger.error(f"Lambda invoke failed: {e}")
        raise HTTPException(status_code=500, detail="분석 요청에 실패했습니다.")

    logger.info(f"Analysis requested: {payload.incident_id}")
    return {"ok": True, "message": "분석 요청이 전송되었습니다."}
