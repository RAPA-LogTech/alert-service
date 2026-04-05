from fastapi import APIRouter, Request, HTTPException
from datetime import datetime
import logging

from ..core.config import get_settings
from ..core.aws_clients import get_dynamodb_resource

logger = logging.getLogger(__name__)

router = APIRouter(tags=["slack"])


@router.post("/events")
async def slack_events(request: Request) -> dict:
    """Slack 이벤트 처리"""
    settings = get_settings()
    body = await request.json()
    
    # URL Verification (구독 확인)
    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge")}
    
    # Slack 서명 검증 (선택사항이지만 권장)
    # verification_token = body.get("token")
    # if verification_token != settings.slack_verification_token:
    #     raise HTTPException(status_code=401, detail="Invalid verification token")
    
    event = body.get("event", {})
    event_type = event.get("type")
    
    try:
        ddb = get_dynamodb_resource()
        table = ddb.Table(settings.ddb_table_slack_messages)
        
        # 이벤트 저장
        if event_type == "message":
            # 메시지 이벤트 처리
            message_item = {
                "pk": f"slack#message",
                "sk": f"{event.get('ts')}#{event.get('user', 'unknown')}",
                "type": "message",
                "user": event.get("user"),
                "text": event.get("text"),
                "ts": event.get("ts"),
                "channel": event.get("channel"),
                "thread_ts": event.get("thread_ts"),
                "created_at": datetime.utcnow().isoformat(),
                "raw_event": body,
            }
            table.put_item(Item=message_item)
            logger.info(f"Saved message event from {event.get('user')} in {event.get('channel')}")
        
        elif event_type == "app_mention":
            # 앱 멘션 처리
            mention_item = {
                "pk": f"slack#mention",
                "sk": f"{event.get('ts')}#{event.get('user')}",
                "type": "mention",
                "user": event.get("user"),
                "text": event.get("text"),
                "ts": event.get("ts"),
                "channel": event.get("channel"),
                "created_at": datetime.utcnow().isoformat(),
                "raw_event": body,
            }
            table.put_item(Item=mention_item)
            logger.info(f"Saved mention event from {event.get('user')}")
        
        else:
            # 그 외 이벤트 저장
            other_item = {
                "pk": f"slack#event#{event_type}",
                "sk": datetime.utcnow().isoformat(),
                "type": event_type,
                "user": event.get("user"),
                "created_at": datetime.utcnow().isoformat(),
                "raw_event": body,
            }
            table.put_item(Item=other_item)
            logger.info(f"Saved {event_type} event")
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"Failed to process Slack event: {e}")
        return {"ok": False, "error": str(e)}

