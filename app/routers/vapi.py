from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import VapiAssistantConfigRequest, VapiAssistantConfigResponse
from app.services.vapi_service import build_assistant_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vapi", tags=["vapi"])


@router.post("/assistant-config", response_model=VapiAssistantConfigResponse)
async def get_assistant_config(body: VapiAssistantConfigRequest) -> VapiAssistantConfigResponse:
    """Return public key and inline assistant configuration for Vapi Web SDK."""
    public_key = settings.VAPI_PUBLIC_KEY.strip()
    if not public_key or public_key.lower() == "your-vapi-public-key-here":
        raise HTTPException(
            status_code=503,
            detail="Vapi public key is missing or placeholder. Set a real VAPI_PUBLIC_KEY in your environment.",
        )

    try:
        assistant_config = build_assistant_config(
            scenario_context=body.scenario_context,
            current_step=body.current_step,
            call_type=body.call_type,
        )
    except Exception as exc:
        logger.exception("Failed to build Vapi assistant config")
        raise HTTPException(status_code=500, detail=f"Failed to build assistant config: {exc}") from exc

    return VapiAssistantConfigResponse(
        public_key=public_key,
        assistant_config=assistant_config,
    )
