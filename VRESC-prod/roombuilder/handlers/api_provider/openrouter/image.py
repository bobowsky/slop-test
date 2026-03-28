"""
OpenRouter image generation via the chat/completions endpoint.

Uses the `modalities` parameter as documented at:
https://openrouter.ai/docs/guides/overview/multimodal/image-generation
"""

import base64
from pathlib import Path

import requests

from .auth import API_BASE, headers

# Default model for image generation (supports 2:1 / wide aspect ratios and
# extended image sizes — good fit for equirectangular panoramas).
DEFAULT_IMAGE_MODEL = "google/gemini-3.1-flash-image-preview"

# Models that output *only* images (no text), requiring modalities=["image"].
# All others use ["image", "text"].
_IMAGE_ONLY_MODELS: set[str] = {
    "black-forest-labs/flux.2-pro",
    "black-forest-labs/flux.2-flex",
    "sourceful/riverflow-v2-fast",
    "sourceful/riverflow-v2-pro",
    "sourceful/riverflow-v2-standard-preview",
    # Image-only on OpenRouter (no route for modalities ["image", "text"]).
    "bytedance-seed/seedream-4.5",
}


def generate_image(
    prompt: str,
    out_path: Path,
    log=print,
    *,
    model: str = DEFAULT_IMAGE_MODEL,
    aspect_ratio: str = "2:1",
    image_size: str = "4K",
    timeout: int = 120,
) -> None:
    """
    Generate a single image via OpenRouter and write it to *out_path*.

    Parameters
    ----------
    prompt       : Text prompt describing the image.
    out_path     : Destination file path (parent directory must exist).
    log          : Callable used for progress messages.
    model        : OpenRouter model identifier.
    aspect_ratio : Requested aspect ratio (e.g. "2:1", "16:9", "1:1").
                   Passed as image_config.aspect_ratio — check model docs for
                   what each model actually honours.
    image_size   : Resolution hint ("1K", "2K", "4K", "0.5K").
    timeout      : HTTP request timeout in seconds.

    Raises
    ------
    RuntimeError on API errors or when no image is returned.
    """
    modalities = ["image"] if model in _IMAGE_ONLY_MODELS else ["image", "text"]

    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": modalities,
        "image_config": {
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        },
    }

    log(f"openrouter: POST {API_BASE}/chat/completions  model={model}")
    resp = requests.post(
        f"{API_BASE}/chat/completions",
        headers=headers(),
        json=payload,
        timeout=timeout,
    )

    if not resp.ok:
        raise RuntimeError(f"OpenRouter API error {resp.status_code}: {resp.text[:500]}")

    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"OpenRouter error: {data['error']}")

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"OpenRouter returned no choices. Response: {data}")

    message = choices[0].get("message", {})
    images = message.get("images") or []

    if not images:
        raise RuntimeError(
            "OpenRouter returned no images in the response. "
            "Check that the model supports image generation and that "
            "`modalities` is set correctly.\n"
            f"Response message content: {message.get('content', '')[:200]}"
        )

    raw_url: str = images[0]["image_url"]["url"]

    if raw_url.startswith("data:"):
        _header, b64 = raw_url.split(",", 1)
        image_bytes = base64.b64decode(b64)
        log(f"openrouter: received base64 image ({len(image_bytes):,} bytes)")
    else:
        log(f"openrouter: downloading image from {raw_url[:80]}…")
        dl = requests.get(raw_url, timeout=timeout)
        dl.raise_for_status()
        image_bytes = dl.content
        log(f"openrouter: downloaded {len(image_bytes):,} bytes")

    out_path.write_bytes(image_bytes)
    log(f"openrouter: image saved → {out_path}")
