from __future__ import annotations

import base64
import json
import logging
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings

_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")
_SCENE_MODEL = "gemini-2.5-flash-lite"

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SceneParams:
    room_id: str
    scene_description: str
    scene_summary: str


class SceneParamsAnalyzer:
    async def analyze_image(self, image_path: Path, room_id: str) -> SceneParams:
        fallback = self._fallback_params(image_path=image_path, room_id=room_id)
        if settings.USE_MOCKS:
            return fallback
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not set — using fallback scene params")
            return fallback

        try:
            return await self._analyze_with_gemini(image_path=image_path, room_id=room_id)
        except Exception as exc:
            logger.warning("Scene analysis failed, using fallback: %s", exc)
            return fallback

    async def _analyze_with_gemini(self, image_path: Path, room_id: str) -> SceneParams:
        mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        image_bytes = image_path.read_bytes()

        prompt = (
            "You are preparing input for a 360 VR room generation pipeline.\n"
            "Analyze the provided room photo and return STRICT JSON with exactly these keys:\n"
            "{\n"
            '  "scene_description": "<140-240 words, vivid but factual scene description>",\n'
            '  "scene_summary": "<1 concise sentence, 18-40 words>"\n'
            "}\n"
            "Rules:\n"
            "- No markdown, no code fences, JSON only.\n"
            "- Focus on physical layout, materials, lighting, and mood.\n"
            "- Keep style cinematic but accurate to the visible scene.\n"
            "- Avoid mentioning people unless clearly visible.\n"
        )

        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = client.models.generate_content(
            model=_SCENE_MODEL,
            contents=[
                types.Part(text=prompt),
                types.Part(inline_data=types.Blob(mime_type=mime, data=image_bytes)),
            ],
        )

        raw = response.candidates[0].content.parts[0].text or ""
        parsed = self._parse_json_text(raw)
        description = self._clean_text(
            parsed.get("scene_description"), fallback="A weathered urban courtyard at sunset."
        )
        summary = self._clean_text(
            parsed.get("scene_summary"),
            fallback="A grounded interior scene in natural light, prepared for an interactive educational experience.",
        )
        return SceneParams(room_id=room_id, scene_description=description, scene_summary=summary)

    def _parse_json_text(self, text: str) -> dict[str, str]:
        stripped = text.strip()
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

        match = _JSON_OBJECT_RE.search(stripped)
        if not match:
            raise RuntimeError("Scene analyzer did not return a JSON object")
        obj = json.loads(match.group(0))
        if not isinstance(obj, dict):
            raise RuntimeError("Scene analyzer JSON root must be an object")
        return obj

    def _fallback_params(self, image_path: Path, room_id: str) -> SceneParams:
        description = (
            "A quiet, atmospheric room prepared for transformation into an educational scenario. "
            "The scene has layered depth, readable object clusters, and strong spatial anchors "
            "that can be converted into interactive learning hotspots in a 360 environment."
        )
        summary = f"A grounded interior scene from {image_path.name}, suitable for 360 conversion and educational hotspot generation."
        return SceneParams(room_id=room_id, scene_description=description, scene_summary=summary)

    def _clean_text(self, value: object, fallback: str) -> str:
        text = str(value or "").strip()
        if not text:
            return fallback
        if len(text) > 4000:
            return text[:4000].rstrip()
        return text
