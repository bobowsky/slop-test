from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import HintRequest, HintResponse
from app.services.interfaces import HintProvider

router = APIRouter(prefix="/api", tags=["hint"])


def _get_hint_provider() -> HintProvider:
    raise NotImplementedError("Overridden at startup via app.dependency_overrides")


@router.post("/hint", response_model=HintResponse)
async def get_hint(
    body: HintRequest,
    provider: HintProvider = Depends(_get_hint_provider),
) -> HintResponse:
    return await provider.get_hint(
        context=body.scenario_context,
        step=body.current_step,
        question=body.user_question,
    )
