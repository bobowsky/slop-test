"""
Gemini image generation via Imagen 3 (generateContent).

Uses google.genai.Client.models.generate_content with response_modalities=["IMAGE"]
and image_config for aspect ratio / size control.

Supported models:
  - imagen-3.0-generate-002   (standard quality, fast)
  - imagen-3.0-fast-generate-001 (lower latency variant)

Note: Imagen 3 on the Gemini Developer API does not support arbitrary aspect
ratios; the accepted values for image_config.aspect_ratio are:
  "1:1", "3:4", "4:3", "9:16", "16:9"
For equirectangular panoramas use "16:9" (closest to 2:1 available).
"""

import base64
from pathlib import Path

from google.genai import types

from .auth import client

DEFAULT_IMAGE_MODEL = "imagen-3.0-generate-002"

# Gemini-supported aspect ratios for Imagen 3.
SUPPORTED_ASPECT_RATIOS = {"1:1", "3:4", "4:3", "9:16", "16:9"}
_FALLBACK_ASPECT_RATIO = "16:9"


def generate_image(
    prompt: str,
    out_path: Path,
    log=print,
    *,
    model: str = DEFAULT_IMAGE_MODEL,
    aspect_ratio: str = "16:9",
    image_size: str = "4K",
    timeout: int = 120,
) -> None:
    """
    Generate a single image via the Gemini Imagen API and write it to *out_path*.

    Parameters
    ----------
    prompt       : Text prompt describing the image.
    out_path     : Destination file path (parent directory must exist).
    log          : Callable used for progress messages.
    model        : Gemini model identifier (default: Imagen 3).
    aspect_ratio : Requested aspect ratio. Must be one of
                   "1:1", "3:4", "4:3", "9:16", "16:9".
                   Unsupported values fall back to "16:9" with a warning.
    image_size   : Resolution hint (informational; Imagen 3 selects its own
                   output resolution — this parameter is accepted for
                   interface parity but not forwarded to the API).
    timeout      : Unused for the SDK path (included for interface parity).

    Raises
    ------
    RuntimeError on API errors or when no image part is returned.
    """
    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        log(
            f"gemini: aspect_ratio '{aspect_ratio}' not supported by Imagen 3"
            f" — falling back to '{_FALLBACK_ASPECT_RATIO}'"
        )
        aspect_ratio = _FALLBACK_ASPECT_RATIO

    log(f"gemini: generate_content  model={model}  aspect_ratio={aspect_ratio}")

    with client() as c:
        response = c.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
            ),
        )

    image_bytes: bytes | None = None
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_bytes = part.inline_data.data
            break

    if image_bytes is None:
        raise RuntimeError(
            f"Gemini returned no image part. Check that the model supports image generation.\nResponse: {response}"
        )

    # inline_data.data may already be raw bytes or a base64 string depending
    # on the SDK version — normalise to bytes.
    if isinstance(image_bytes, str):
        image_bytes = base64.b64decode(image_bytes)

    out_path.write_bytes(image_bytes)
    log(f"gemini: image saved → {out_path} ({len(image_bytes):,} bytes)")
