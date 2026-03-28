from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from app.config import UPLOADS_DIR, settings
from app.models.schemas import GenerateAccepted, ProgressEvent
from app.services.roombuilder import RoomBuilderService
from app.services.scenario_builder import build_scenario_from_room

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generate"])

_jobs: dict[str, dict[str, Any]] = {}
_roombuilder_service = RoomBuilderService()

_ALLOWED_CATEGORIES: set[str] = {"The Archive", "The Cold Case"}

PROGRESS_FLOW: list[tuple[str, str]] = [
    ("analyzing_scene", "Analyzing uploaded scene..."),
    ("generating_panorama", "Generating 360 panorama..."),
    ("detecting_animatables", "Identifying animated elements..."),
    ("generating_music", "Composing ambient soundtrack..."),
    ("generating_video", "Creating animated 360 video..."),
    ("grounding_hotspots", "Locating interactive hotspots..."),
    ("generating_hotspot_content", "Creating interactive hotspot content..."),
    ("writing_room_files", "Assembling room files..."),
    ("generating_puzzles", "Compiling learning scenario..."),
    ("preparing_results", "Preparing result payload..."),
]
_PROGRESS_INDEX: dict[str, int] = {key: idx for idx, (key, _label) in enumerate(PROGRESS_FLOW, start=1)}
_PROGRESS_LABELS: dict[str, str] = dict(PROGRESS_FLOW)
_STAGE_TO_PROGRESS_KEY: dict[str, str] = {
    "scene_analyze": "analyzing_scene",
    "image_generate": "generating_panorama",
    "detect_animatables": "detecting_animatables",
    "music_generate": "generating_music",
    "video_generate": "generating_video",
    "hotspot_grounding": "grounding_hotspots",
    "hotspot_content": "generating_hotspot_content",
    "write_hotspot_json": "writing_room_files",
    "write_hotspot_interfaces": "writing_room_files",
    "deploy_room": "writing_room_files",
}


@router.post("/generate", response_model=GenerateAccepted)
async def start_generation(
    image: UploadFile,
    theme: str = "The Archive",
    mode: str = "Explore",
    difficulty: str = "Medium",
) -> GenerateAccepted:
    if image.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {image.content_type}. Allowed: {', '.join(settings.ALLOWED_MIME_TYPES)}",
        )

    normalized_theme = _normalize_category(theme)

    ext = image.filename.rsplit(".", 1)[-1] if image.filename and "." in image.filename else "jpg"
    job_id = uuid.uuid4().hex[:12]
    filename = f"{job_id}.{ext}"
    file_path = UPLOADS_DIR / filename
    room_id = f"{settings.ROOM_ID_PREFIX}_active"

    content = await image.read()
    file_path.write_bytes(content)

    original_image_url = f"/uploads/{filename}"

    _jobs[job_id] = {
        "image_path": str(file_path),
        "original_image_url": original_image_url,
        "theme": normalized_theme,
        "mode": mode,
        "difficulty": difficulty,
        "room_id": room_id,
    }

    return GenerateAccepted(job_id=job_id, original_image_url=original_image_url)


@router.get("/generate/{job_id}/stream")
async def stream_generation(job_id: str) -> EventSourceResponse:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _jobs[job_id]

    async def event_stream():
        progress_keys_seen: set[str] = set()
        try:
            # Run VRESC roombuilder (scene analysis is now step 0 inside the pipeline).
            stage_queue: asyncio.Queue[str] = asyncio.Queue()

            async def _on_stage(stage_name: str) -> None:
                await stage_queue.put(stage_name)

            build_task = asyncio.create_task(
                _roombuilder_service.run(
                    room_id=job["room_id"],
                    image_path=Path(job["image_path"]),
                    on_stage=_on_stage,
                )
            )

            while True:
                if build_task.done() and stage_queue.empty():
                    break
                try:
                    stage_name = await asyncio.wait_for(stage_queue.get(), timeout=0.2)
                except TimeoutError:
                    await asyncio.sleep(0)
                    continue

                progress_key = _STAGE_TO_PROGRESS_KEY.get(stage_name)
                if not progress_key or progress_key in progress_keys_seen:
                    continue
                progress_keys_seen.add(progress_key)
                yield _progress_event_for_key(progress_key)

            build_result = await build_task

            # 3) Build Room2Learn scenario JSON from generated VRESC room.
            if "generating_puzzles" not in progress_keys_seen:
                yield _progress_event_for_key("generating_puzzles")
                progress_keys_seen.add("generating_puzzles")

            scenario = build_scenario_from_room(
                room_id=job["room_id"],
                room_dir=build_result.room_dir,
                original_image_url=job["original_image_url"],
                theme=job["theme"],
                mode=job["mode"],
                difficulty=job["difficulty"],
            )

            if "preparing_results" not in progress_keys_seen:
                yield _progress_event_for_key("preparing_results")
                progress_keys_seen.add("preparing_results")

            # Final: complete event with full scenario.
            yield {
                "event": "complete",
                "data": scenario.model_dump_json(),
            }
        except Exception as exc:
            logger.exception("Generation pipeline failed for job %s", job_id)
            yield {
                "event": "failed",
                "data": str(exc),
            }
        finally:
            _jobs.pop(job_id, None)

    return EventSourceResponse(event_stream())


def _progress_event_for_key(progress_key: str) -> dict[str, str]:
    step = _PROGRESS_INDEX[progress_key]
    label = _PROGRESS_LABELS[progress_key]
    event = ProgressEvent(step=step, total=len(PROGRESS_FLOW), label=label)
    return {
        "event": "progress",
        "data": event.model_dump_json(),
    }


def _normalize_category(raw_theme: str) -> str:
    theme = (raw_theme or "").strip()
    if not theme:
        return "The Archive"
    if theme in _ALLOWED_CATEGORIES:
        return theme
    raise HTTPException(
        status_code=400,
        detail="Invalid category. Allowed values: The Archive, The Cold Case",
    )
