"""
Gemini vision / multimodal chat via generateContent.

Encodes a local image as inline_data and sends it together with a text
prompt to any vision-capable Gemini model.
"""

import base64
import json
import re
from pathlib import Path
from typing import Union

from google.genai import types

from .auth import client

DEFAULT_VISION_MODEL = "gemini-2.5-flash-lite"


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
    Send a text prompt together with an image to a Gemini vision model.

    Parameters
    ----------
    prompt     : Text prompt (system + user instructions combined).
    image_path : Path to the image file to attach.
    log        : Callable used for progress messages.
    model      : Gemini model identifier.
    timeout    : Unused for the SDK path (included for interface parity).
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

    log(f"gemini: generate_content  model={model}  image={image_path.name} ({len(image_bytes):,} bytes)")

    with client() as c:
        response = c.models.generate_content(
            model=model,
            contents=[
                types.Part(text=prompt),
                types.Part(inline_data=types.Blob(mime_type=mime, data=base64.b64decode(b64))),
            ],
        )

    content: str = response.candidates[0].content.parts[0].text or ""

    if not parse_json:
        return content

    stripped = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped.strip())

    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini response is not valid JSON: {exc}\nRaw content: {content[:500]}") from exc
