from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/slack", tags=["slack"])


@router.post("/events")
def slack_events() -> dict:
    raise HTTPException(status_code=501, detail="not implemented")
