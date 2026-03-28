from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from app.config import VRESC_ARTIFACTS_DIR
from app.models.schemas import FinalEscape, PuzzleStep, ScenarioResponse, Transformation, VapiConfig

_INTERACTIVE_TYPES = {"numpad", "toggle-bank"}


def build_scenario_from_room(
    *,
    room_id: str,
    room_dir: Path,
    original_image_url: str,
    theme: str,
    mode: str,
    difficulty: str,
) -> ScenarioResponse:
    room_layout = _read_json(room_dir / f"{room_id}.json")
    hotspots = _collect_hotspots(room_layout=room_layout, room_dir=room_dir)

    scene_data = _load_scene_data(room_dir)

    transformations = _build_transformations(hotspots)
    puzzles = _build_puzzles(hotspots)
    final_escape = _build_final_escape(puzzles)

    panorama_url = _first_existing_asset(
        room_id=room_id,
        room_dir=room_dir,
        candidates=("panorama.jpg", "panorama.png", "panorama.jpeg", "panorama.webp"),
    )
    generated_image_url = panorama_url or original_image_url
    viewer_url = f"/static/viewer.html?room={room_id}"
    intro = _build_intro(hotspots)

    return ScenarioResponse(
        experience_id=f"R2L-{uuid.uuid4().hex[:8].upper()}",
        status="ready",
        title=f"Room {room_id}",
        theme=theme,
        mode=mode,
        difficulty=difficulty,
        story=scene_data.get("scene_description", "An interactive 360 experience."),
        detected_objects=_detect_objects_from_hotspots(hotspots),
        transformations=transformations,
        puzzles=puzzles,
        final_escape=final_escape,
        voice_host_intro=intro,
        original_image_url=original_image_url,
        generated_image_url=generated_image_url,
        transformed_image_prompt=scene_data.get("scene_summary", ""),
        vapi_config=VapiConfig(
            intro_message=intro,
            persona=(
                "You are the knowledge guide of a 360 educational portal. Keep responses short, engaging, "
                "and focused on the learner's current challenge."
            ),
            guardrails=(
                "Never reveal the final answer directly. Provide only progressive hints tied to the current task."
            ),
        ),
        room_id=room_id,
        viewer_url=viewer_url,
        panorama_thumbnail_url=generated_image_url,
    )


def _load_scene_data(room_dir: Path) -> dict[str, str]:
    """Load scene data from the deployed room dir or the artifacts staging area."""
    for candidate in (
        room_dir / "scene_analyze.json",
        VRESC_ARTIFACTS_DIR / room_dir.name / "scene_analyze.json",
    ):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return {}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_hotspots(*, room_layout: dict[str, Any], room_dir: Path) -> list[dict[str, Any]]:
    hotspots_dir = room_dir / "hotspots"
    result: list[dict[str, Any]] = []
    for hotspot in room_layout.get("hotspots", []):
        if not isinstance(hotspot, dict):
            continue
        hs_id = str(hotspot.get("id", "")).strip()
        if not hs_id:
            continue
        hs_payload = {
            "id": hs_id,
            "polygon": hotspot.get("polygon"),
            "popup": {},
        }
        hs_json = hotspots_dir / hs_id / "hotspot.json"
        if hs_json.exists():
            data = _read_json(hs_json)
            popup = data.get("popup", {})
            if isinstance(popup, dict):
                hs_payload["popup"] = popup
        result.append(hs_payload)
    return result


def _build_transformations(hotspots: list[dict[str, Any]]) -> list[Transformation]:
    rows: list[Transformation] = []
    for hotspot in hotspots[:8]:
        popup = hotspot.get("popup", {})
        interaction = str(popup.get("interaction", "info"))
        rows.append(
            Transformation(
                real_object=_humanize_hotspot_id(str(hotspot.get("id", ""))),
                game_object=str(popup.get("title", _humanize_hotspot_id(str(hotspot.get("id", ""))))),
                puzzle_role=_interaction_to_role(interaction),
            )
        )
    if rows:
        return rows
    return [
        Transformation(
            real_object="Scene anchor",
            game_object="Primary hotspot",
            puzzle_role="Interaction node",
        )
    ]


def _build_puzzles(hotspots: list[dict[str, Any]]) -> list[PuzzleStep]:
    interactive = [
        hs for hs in hotspots if str(hs.get("popup", {}).get("interaction", "")).strip().lower() in _INTERACTIVE_TYPES
    ]
    source = interactive[:3] if interactive else hotspots[:3]

    puzzles: list[PuzzleStep] = []
    for index, hotspot in enumerate(source, start=1):
        popup = hotspot.get("popup", {})
        title = str(popup.get("title", _humanize_hotspot_id(str(hotspot.get("id", "")))))
        description = str(
            popup.get("prompt") or popup.get("body") or f"Inspect {title} and complete the interactive task."
        )
        hint = str(
            popup.get("hint") or popup.get("on_fail") or "Use nearby visual clues and interact with this hotspot."
        )
        solution = _extract_solution_text(popup)
        puzzles.append(
            PuzzleStep(
                step=index,
                title=title,
                description=description,
                hint=hint,
                solution=solution,
            )
        )

    if puzzles:
        return puzzles

    return [
        PuzzleStep(
            step=1,
            title="Survey The Room",
            description="Explore the 360 scene and identify a key visual clue.",
            hint="Focus on a single standout object and inspect it carefully.",
            solution="Any clearly observed key object in the scene.",
        )
    ]


def _build_final_escape(puzzles: list[PuzzleStep]) -> FinalEscape:
    digit_fragments = [re.sub(r"\D+", "", step.solution) for step in puzzles]
    digit_fragments = [frag for frag in digit_fragments if frag]
    if digit_fragments:
        solution = "".join(fragment[0] for fragment in digit_fragments)[:6]
    else:
        solution = str(len(puzzles)).zfill(3)
    return FinalEscape(
        objective="Enter the final sequence derived from solved hotspot challenges.",
        solution=solution,
    )


def _build_intro(hotspots: list[dict[str, Any]]) -> str:
    if not hotspots:
        return "Welcome, explorer. Your learning portal is ready. Begin by inspecting the first point of interest."
    first = hotspots[0]
    title = str(first.get("popup", {}).get("title") or _humanize_hotspot_id(str(first.get("id", ""))))
    return f"Welcome, explorer. Your 360 learning portal is active. Begin with {title}."


def _detect_objects_from_hotspots(hotspots: list[dict[str, Any]]) -> list[str]:
    objects: list[str] = []
    for hotspot in hotspots:
        objects.append(_humanize_hotspot_id(str(hotspot.get("id", ""))).lower())
        if len(objects) >= 5:
            break
    if objects:
        return objects
    return ["room interior", "knowledge anchor", "interactive hotspot"]


def _extract_solution_text(popup: dict[str, Any]) -> str:
    answer = popup.get("answer")
    if answer is not None:
        return str(answer)
    target = popup.get("target")
    if isinstance(target, list) and target:
        bits = ["ON" if bool(value) else "OFF" for value in target]
        return " / ".join(bits)
    return str(popup.get("title", "Observe the scene and infer the correct interaction."))


def _humanize_hotspot_id(raw_id: str) -> str:
    text = raw_id.strip()
    if text.startswith("hs_"):
        text = text[3:]
    text = text.replace("_", " ").strip()
    if not text:
        return "Unknown hotspot"
    return " ".join(word.capitalize() for word in text.split())


def _interaction_to_role(interaction: str) -> str:
    normalized = interaction.strip().lower()
    if normalized == "numpad":
        return "Knowledge challenge"
    if normalized == "toggle-bank":
        return "Logic task"
    return "Information hotspot"


def _first_existing_asset(*, room_id: str, room_dir: Path, candidates: tuple[str, ...]) -> str | None:
    for name in candidates:
        if (room_dir / name).exists():
            return f"/content/rooms/{room_id}/{name}"
    return None
