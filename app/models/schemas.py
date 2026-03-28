from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SceneAnalysis(BaseModel):
    """Output of the scene analysis step."""

    detected_objects: list[str] = Field(..., min_length=3, max_length=5)
    mood: str
    puzzle_anchors: list[str]


class Transformation(BaseModel):
    real_object: str
    game_object: str
    puzzle_role: str


class PuzzleStep(BaseModel):
    step: int
    title: str
    description: str
    hint: str
    solution: str


class FinalEscape(BaseModel):
    objective: str
    solution: str


class VapiConfig(BaseModel):
    intro_message: str
    persona: str
    guardrails: str
    vocal_style: str = "warm, engaging, and educational"


class ScenarioResponse(BaseModel):
    """Canonical response object returned to the frontend."""

    experience_id: str
    status: str = "ready"
    title: str
    theme: str
    mode: str
    difficulty: str
    story: str
    detected_objects: list[str]
    transformations: list[Transformation]
    puzzles: list[PuzzleStep]
    final_escape: FinalEscape
    voice_host_intro: str
    original_image_url: str
    generated_image_url: str
    transformed_image_prompt: str
    vapi_config: VapiConfig
    room_id: str = ""
    viewer_url: str = ""
    panorama_thumbnail_url: str = ""


class GenerateAccepted(BaseModel):
    """Returned immediately by POST /api/generate."""

    job_id: str
    original_image_url: str


class ProgressEvent(BaseModel):
    """SSE progress event payload."""

    step: int
    total: int = 4
    label: str
    status: str = "processing"


class HintRequest(BaseModel):
    scenario_context: dict
    current_step: int = Field(..., ge=1, le=3)
    user_question: str | None = None


class HintResponse(BaseModel):
    hint: str
    voice_friendly: str


class VapiAssistantConfigRequest(BaseModel):
    scenario_context: dict
    current_step: int = Field(..., ge=1)
    call_type: str = "intro"


class VapiAssistantConfigResponse(BaseModel):
    public_key: str
    assistant_config: dict[str, Any]


class HealthResponse(BaseModel):
    status: str = "ok"
    mock_mode: bool
