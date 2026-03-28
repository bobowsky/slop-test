"""
OpenRouter API provider package.

Exposes a concrete ``OpenRouterProvider`` that implements ``ApiProvider``,
plus the individual module-level functions for callers that import them
directly by name.
"""

from pathlib import Path
from typing import Callable, Union

from ..base import ApiProvider
from .audio import DEFAULT_AUDIO_FORMAT, DEFAULT_AUDIO_MODEL, DEFAULT_AUDIO_VOICE, generate_audio
from .chat import DEFAULT_CHAT_MODEL, chat_text
from .image import DEFAULT_IMAGE_MODEL, generate_image
from .vision import DEFAULT_VISION_MODEL, chat_vision

__all__ = [
    "OpenRouterProvider",
    # module-level helpers kept for backward-compatible direct imports
    "generate_image",
    "generate_audio",
    "chat_text",
    "chat_vision",
    "DEFAULT_IMAGE_MODEL",
    "DEFAULT_AUDIO_MODEL",
    "DEFAULT_AUDIO_VOICE",
    "DEFAULT_AUDIO_FORMAT",
    "DEFAULT_CHAT_MODEL",
    "DEFAULT_VISION_MODEL",
]


class OpenRouterProvider(ApiProvider):
    """Concrete ``ApiProvider`` backed by the OpenRouter API."""

    def generate_image(
        self,
        prompt: str,
        out_path: Path,
        log: Callable = print,
        *,
        model: str = DEFAULT_IMAGE_MODEL,
        aspect_ratio: str = "2:1",
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
        voice: str = DEFAULT_AUDIO_VOICE,
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
        image_path: "Path | None" = None,
        model: str = "",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        poll_interval: int = 15,
        timeout: int = 600,
    ) -> None:
        raise NotImplementedError(
            "OpenRouter does not provide a video generation API. Use GeminiProvider for video generation."
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
