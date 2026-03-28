from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import VRESC_ROOMS_DIR

router = APIRouter(prefix="/api/scene", tags=["scene"])

_SAFE_ROOM_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_VIDEO_CANDIDATES = ("video.mp4", "video.webm")
_IMAGE_CANDIDATES = ("panorama.jpg", "panorama.png", "panorama.jpeg", "panorama.webp")
_AUDIO_CANDIDATES = ("music.mp3", "music.ogg", "music.wav")


def _validate_room_id(room_id: str) -> str:
    cleaned = room_id.strip()
    if not cleaned or not _SAFE_ROOM_ID.fullmatch(cleaned):
        raise HTTPException(status_code=400, detail="Invalid room id")
    return cleaned


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Missing file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in {path.name}") from exc


def _first_asset(room_dir: Path, names: tuple[str, ...], room_id: str) -> str | None:
    for name in names:
        if (room_dir / name).exists():
            return f"/content/rooms/{room_id}/{name}"
    return None


def _merge_hotspot_content(room_dir: Path, scene_data: dict[str, Any]) -> None:
    hotspots = scene_data.get("hotspots")
    if not isinstance(hotspots, list):
        return

    hotspots_dir = room_dir / "hotspots"
    for hotspot in hotspots:
        if not isinstance(hotspot, dict):
            continue
        hotspot_id = str(hotspot.get("id", "")).strip()
        if not hotspot_id:
            continue
        hs_path = hotspots_dir / hotspot_id / "hotspot.json"
        if not hs_path.exists():
            continue
        hs_data = _load_json(hs_path)
        if not hotspot.get("desc") and hs_data.get("desc"):
            hotspot["desc"] = hs_data["desc"]
        if "popup" not in hotspot and hs_data.get("popup"):
            hotspot["popup"] = hs_data["popup"]


@router.get("/{room_id}")
async def get_scene(room_id: str) -> dict[str, Any]:
    safe_room_id = _validate_room_id(room_id)
    room_dir = VRESC_ROOMS_DIR / safe_room_id
    scene_path = room_dir / f"{safe_room_id}.json"

    if not scene_path.exists():
        raise HTTPException(status_code=404, detail=f"Room not found: {safe_room_id}")

    scene_data = _load_json(scene_path)
    scene_data["room"] = safe_room_id

    video = _first_asset(room_dir, _VIDEO_CANDIDATES, safe_room_id)
    image = _first_asset(room_dir, _IMAGE_CANDIDATES, safe_room_id)
    audio = _first_asset(room_dir, _AUDIO_CANDIDATES, safe_room_id)
    if video:
        scene_data["video"] = video
    if image:
        scene_data["image"] = image
    if audio:
        scene_data["audio"] = audio

    _merge_hotspot_content(room_dir, scene_data)
    return scene_data
