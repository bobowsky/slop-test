"""
OpenRouter vision / multimodal chat via the chat/completions endpoint.

Encodes a local image as a base64 data-URL and sends it together with a
text prompt to any vision-capable model available on OpenRouter.
"""

import base64
import json
import re
from pathlib import Path
from typing import Union

import requests

from .auth import API_BASE, headers

DEFAULT_VISION_MODEL = "google/gemini-2.5-flash-lite"


def chat_vision(
    prompt: str,
    image_path: Path,
    log=print,
    *,
    model: str = DEFAULT_VISION_MODEL,
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
    model      : OpenRouter model identifier.
    timeout    : HTTP request timeout in seconds.
    parse_json : If True (default), strip markdown fences and parse the
                 response as JSON, returning a dict/list.
                 If False, return the raw response string.

    Returns
    -------
    Parsed JSON object (dict or list) when parse_json=True, or a plain str.

    Raises
    ------
    RuntimeError on API errors or when parse_json=True and the response
    cannot be parsed as JSON.
    """
    image_bytes = image_path.read_bytes()
    suffix = image_path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
    b64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:{mime};base64,{b64}"

    payload: dict = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    }

    log(
        f"openrouter: POST {API_BASE}/chat/completions"
        f"  model={model}  image={image_path.name} ({len(image_bytes):,} bytes)"
    )
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

    content: str = choices[0].get("message", {}).get("content", "")

    if not parse_json:
        return content

    stripped = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped.strip())

    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenRouter response is not valid JSON: {exc}\nRaw content: {content[:500]}") from exc
