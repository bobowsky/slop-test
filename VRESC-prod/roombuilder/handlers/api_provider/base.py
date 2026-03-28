"""
Abstract base class for API providers used in the roombuilder pipeline.

Concrete providers (e.g. OpenRouter) implement this interface so that
higher-level handlers can remain provider-agnostic.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Union


class ApiProvider(ABC):
    """
    Interface contract for a roombuilder API provider.

    Every method that a handler may call must appear here so that
    alternative provider implementations stay drop-in compatible.
    """

    # ------------------------------------------------------------------
    # Image generation
    # ------------------------------------------------------------------

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        out_path: Path,
        log: Callable = print,
        *,
        model: str,
        aspect_ratio: str = "2:1",
        image_size: str = "4K",
        timeout: int = 120,
    ) -> None:
        """
        Generate a single image from *prompt* and write it to *out_path*.

        Parameters
        ----------
        prompt       : Text prompt describing the image.
        out_path     : Destination file path (parent directory must exist).
        log          : Callable used for progress messages.
        model        : Provider model identifier.
        aspect_ratio : Requested aspect ratio (e.g. "2:1", "16:9", "1:1").
        image_size   : Resolution hint ("1K", "2K", "4K").
        timeout      : HTTP request timeout in seconds.
        """

    # ------------------------------------------------------------------
    # Audio generation
    # ------------------------------------------------------------------

    @abstractmethod
    def generate_audio(
        self,
        prompt: str,
        out_path: Path,
        log: Callable = print,
        *,
        model: str,
        voice: str,
        audio_format: str = "mp3",
        timeout: int = 180,
    ) -> None:
        """
        Generate audio from *prompt* and write it to *out_path*.

        Parameters
        ----------
        prompt       : Text prompt for the audio model.
        out_path     : Destination file path (extension should match audio_format).
        log          : Callable used for progress messages.
        model        : Provider model identifier.
        voice        : Voice identifier (provider-specific, e.g. "alloy").
        audio_format : Audio container ("mp3", "wav", "flac", "opus", "aac").
        timeout      : HTTP request timeout in seconds.
        """

    # ------------------------------------------------------------------
    # Video generation
    # ------------------------------------------------------------------

    @abstractmethod
    def generate_video(
        self,
        prompt: str,
        out_path: Path,
        log: Callable = print,
        *,
        image_path: "Path | None" = None,
        model: str,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        poll_interval: int = 15,
        timeout: int = 600,
    ) -> None:
        """
        Generate a video from *prompt* and write it to *out_path*.

        Parameters
        ----------
        prompt           : Text prompt describing the video.
        out_path         : Destination file path (.mp4).
        log              : Callable used for progress messages.
        image_path       : Optional image used as the first frame (image-to-video).
        model            : Provider model identifier.
        aspect_ratio     : "16:9" (landscape) or "9:16" (portrait).
        duration_seconds : Target clip duration in seconds.
        poll_interval    : Seconds between long-running operation status polls.
        timeout          : Max seconds to wait before raising RuntimeError.
        """

    # ------------------------------------------------------------------
    # Text-only chat
    # ------------------------------------------------------------------

    @abstractmethod
    def chat_text(
        self,
        prompt: str,
        log: Callable = print,
        *,
        model: str,
        timeout: int = 120,
        parse_json: bool = False,
    ) -> Union[dict, list, str]:
        """
        Send a text-only prompt to a language model.

        Parameters
        ----------
        prompt     : Full prompt text (system + user instructions combined).
        log        : Callable used for progress messages.
        model      : Provider model identifier.
        timeout    : HTTP request timeout in seconds.
        parse_json : When True strip markdown fences and return parsed JSON.
                     When False (default) return the raw response string.

        Returns
        -------
        Parsed JSON object (dict or list) when parse_json=True, else str.
        """

    # ------------------------------------------------------------------
    # Vision / multimodal chat
    # ------------------------------------------------------------------

    @abstractmethod
    def chat_vision(
        self,
        prompt: str,
        image_path: Path,
        log: Callable = print,
        *,
        model: str,
        timeout: int = 120,
        parse_json: bool = True,
    ) -> Union[dict, list, str]:
        """
        Send a text prompt together with an image to a vision-capable model.

        Parameters
        ----------
        prompt     : Text prompt (system + user instructions combined).
        image_path : Path to the image file to attach.
        log        : Callable used for progress messages.
        model      : Provider model identifier.
        timeout    : HTTP request timeout in seconds.
        parse_json : When True strip markdown fences and return parsed JSON.
                     When False return the raw response string.

        Returns
        -------
        Parsed JSON object (dict or list) when parse_json=True, else str.
        """
