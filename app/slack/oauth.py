from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/slack", tags=["slack"])


@router.get("/oauth/connect")
def slack_connect() -> dict:
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("/oauth/callback")
def slack_callback() -> dict:
    raise HTTPException(status_code=501, detail="not implemented")
