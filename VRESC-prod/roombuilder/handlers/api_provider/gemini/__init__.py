"""
Gemini API provider package (Google AI Studio).

Exposes a concrete ``GeminiProvider`` that implements ``ApiProvider``,
plus the individual module-level functions for direct imports.

Capability mapping
------------------
  generate_image  →  Imagen 3  (imagen-3.0-generate-002)
  generate_audio  →  Lyria 3   (lyria-3-clip-preview / lyria-3-pro-preview)
  generate_video  →  Veo 3.1   (veo-3.1-generate-preview)
  chat_vision     →  Gemini 2.5 Flash Lite

Requires GOOGLE_API_KEY in the project root .env (or as an env variable).
"""

from pathlib import Path
from typing import Callable, Union

from ..base import ApiProvider
from .audio import DEFAULT_AUDIO_FORMAT, DEFAULT_AUDIO_MODEL, generate_audio
from .chat import DEFAULT_CHAT_MODEL, chat_text
from .image import DEFAULT_IMAGE_MODEL, generate_image
from .video import DEFAULT_VIDEO_MODEL, generate_video
from .vision import DEFAULT_VISION_MODEL, chat_vision

__all__ = [
    "GeminiProvider",
    # module-level helpers for direct imports
    "generate_image",
    "generate_audio",
    "generate_video",
    "chat_text",
    "chat_vision",
    "DEFAULT_IMAGE_MODEL",
    "DEFAULT_AUDIO_MODEL",
    "DEFAULT_AUDIO_FORMAT",
    "DEFAULT_CHAT_MODEL",
    "DEFAULT_VIDEO_MODEL",
    "DEFAULT_VISION_MODEL",
]


class GeminiProvider(ApiProvider):
    """Concrete ``ApiProvider`` backed by the Google Gemini Developer API."""

    def generate_image(
        self,
        prompt: str,
        out_path: Path,
        log: Callable = print,
        *,
        model: str = DEFAULT_IMAGE_MODEL,
        aspect_ratio: str = "16:9",
        image_size: str = "4K",
        timeout: int = 120,
    ) -> None:
        generate_image(
            prompt,
            out_path,
            log,
            model=model,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            timeout=timeout,
        )

    def generate_audio(
        self,
        prompt: str,
        out_path: Path,
        log: Callable = print,
        *,
        model: str = DEFAULT_AUDIO_MODEL,
        voice: str = "",
        audio_format: str = DEFAULT_AUDIO_FORMAT,
        timeout: int = 180,
    ) -> None:
        generate_audio(
            prompt,
            out_path,
            log,
            model=model,
            voice=voice,
            audio_format=audio_format,
            timeout=timeout,
        )

    def chat_text(
        self,
        prompt: str,
        log: Callable = print,
        *,
        model: str = DEFAULT_CHAT_MODEL,
        timeout: int = 120,
        parse_json: bool = False,
    ) -> Union[dict, list, str]:
        return chat_text(
            prompt,
            log,
            model=model,
            timeout=timeout,
            parse_json=parse_json,
        )

    def generate_video(
        self,
        prompt: str,
        out_path: Path,
        log: Callable = print,
        *,
        image_path: Path | None = None,
        model: str = DEFAULT_VIDEO_MODEL,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        poll_interval: int = 15,
        timeout: int = 600,
    ) -> None:
        generate_video(
            prompt,
            out_path,
            log,
            image_path=image_path,
            model=model,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            poll_interval=poll_interval,
            timeout=timeout,
        )

    def chat_vision(
        self,
        prompt: str,
        image_path: Path,
        log: Callable = print,
        *,
        model: str = DEFAULT_VISION_MODEL,
        timeout: int = 120,
        parse_json: bool = True,
    ) -> Union[dict, list, str]:
        return chat_vision(
            prompt,
            image_path,
            log,
            model=model,
            timeout=timeout,
            parse_json=parse_json,
        )
