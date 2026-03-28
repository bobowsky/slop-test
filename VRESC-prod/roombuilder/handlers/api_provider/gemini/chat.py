"""
Gemini plain text chat via generateContent.

Used for LLM-only steps that require no image input (e.g. hotspot_content).
"""

import json
import re
from typing import Union

from .auth import client

DEFAULT_CHAT_MODEL = "gemini-2.5-flash-lite"


def chat_text(
    prompt: str,
    log=print,
    *,
    model: str = DEFAULT_CHAT_MODEL,
    timeout: int = 120,
    parse_json: bool = False,
) -> Union[dict, list, str]:
    """
    Send a text-only prompt to a Gemini language model.

    Parameters
    ----------
    prompt     : Full prompt text (system + user instructions combined).
    log        : Callable used for progress messages.
    model      : Gemini model identifier.
    timeout    : Unused for the SDK path (included for interface parity).
    parse_json : If True, strip markdown fences and parse response as JSON.
                 If False (default), return the raw response string.

    Returns
    -------
    Parsed JSON object (dict or list) when parse_json=True, or a plain str.

    Raises
    ------
    RuntimeError on API errors or when parse_json=True and the response
    cannot be parsed as JSON.
    """
    log(f"gemini: generate_content  model={model}")

    with client() as c:
        response = c.models.generate_content(
            model=model,
            contents=prompt,
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
