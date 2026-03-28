"""
Gemini video generation via Veo 3.1 (generate_videos — long-running operation).

Supports both text-to-video and image-to-video (panorama.jpg as first frame).
The operation is polled until complete, then the video bytes are saved locally.

Available models:
  veo-3.1-generate-preview       — high quality, 8-second 720p/1080p/4K + audio
  veo-3.1-fast-generate-preview  — lower latency variant

References:
  https://ai.google.dev/gemini-api/docs/video
"""

import time
from pathlib import Path

from google.genai import types

from .auth import client

DEFAULT_VIDEO_MODEL = "veo-3.1-generate-preview"
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_DURATION_SECONDS = 8
DEFAULT_POLL_INTERVAL = 15  # seconds between status checks


def generate_video(
    prompt: str,
    out_path: Path,
    log=print,
    *,
    image_path: Path | None = None,
    model: str = DEFAULT_VIDEO_MODEL,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    duration_seconds: int = DEFAULT_DURATION_SECONDS,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    timeout: int = 600,
) -> None:
    """
    Generate a video via Veo 3.1 and write it to *out_path*.

    When *image_path* is provided the image is used as the first frame
    (image-to-video).  Otherwise pure text-to-video is performed.

    Parameters
    ----------
    prompt           : Text prompt describing the video.
    out_path         : Destination file path (.mp4).
    log              : Callable used for progress messages.
    image_path       : Optional path to an image used as the first frame.
    model            : Veo model identifier.
    aspect_ratio     : "16:9" (landscape) or "9:16" (portrait).
    duration_seconds : Target duration (Veo 3.1 generates ~8-second clips).
    poll_interval    : Seconds between operation status polls.
    timeout          : Max seconds to wait for the operation to complete.

    Raises
    ------
    RuntimeError on API errors, timeout, or when no video is returned.
    """
    config = types.GenerateVideosConfig(
        aspect_ratio=aspect_ratio,
        duration_seconds=duration_seconds,
        number_of_videos=1,
    )

    image: types.Image | None = None
    if image_path is not None:
        image_bytes = image_path.read_bytes()
        suffix = image_path.suffix.lower().lstrip(".")
        mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
        image = types.Image(image_bytes=image_bytes, mime_type=mime)
        log(f"gemini: image-to-video  first_frame={image_path.name} ({len(image_bytes):,} bytes)")

    log(f"gemini: generate_videos  model={model}  aspect_ratio={aspect_ratio}")

    with client() as c:
        operation = c.models.generate_videos(
            model=model,
            prompt=prompt,
            image=image,
            config=config,
        )

        elapsed = 0
        while not operation.done:
            if elapsed >= timeout:
                raise RuntimeError(
                    f"Veo video generation timed out after {timeout}s. "
                    "The operation may still be running on the server."
                )
            log(f"gemini: waiting for video… ({elapsed}s elapsed)")
            time.sleep(poll_interval)
            elapsed += poll_interval
            operation = c.operations.get(operation)

    generated_videos = operation.response.generated_videos
    if not generated_videos:
        raise RuntimeError(f"Veo returned no generated videos. Full operation response: {operation.response}")

    video = generated_videos[0].video

    # video.video_bytes contains the raw MP4 if already downloaded;
    # otherwise download via the file URI.
    if video.video_bytes:
        video_bytes = video.video_bytes
        log(f"gemini: received {len(video_bytes):,} bytes inline")
    else:
        log("gemini: downloading video from URI…")
        with client() as c:
            c.files.download(file=video)
        video_bytes = video.video_bytes

    if not video_bytes:
        raise RuntimeError("Veo video bytes are empty after download.")

    out_path.write_bytes(video_bytes)
    log(f"gemini: video saved → {out_path} ({len(video_bytes):,} bytes)")
