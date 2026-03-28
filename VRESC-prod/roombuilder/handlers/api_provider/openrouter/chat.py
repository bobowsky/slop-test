"""
OpenRouter plain text chat via the chat/completions endpoint.

Used for LLM-only steps that require no image input (e.g. hotspot_content).
"""

import json
import re
from typing import Union

import requests

from .auth import API_BASE, headers

DEFAULT_CHAT_MODEL = "google/gemini-2.5-flash-lite"


def chat_text(
    prompt: str,
    log=print,
    *,
    model: str = DEFAULT_CHAT_MODEL,
    timeout: int = 120,
    parse_json: bool = False,
) -> Union[dict, list, str]:
    """
    Send a text-only prompt to a language model via OpenRouter.

    Parameters
    ----------
    prompt     : Full prompt text (system + user instructions combined).
    log        : Callable used for progress messages.
    model      : OpenRouter model identifier.
    timeout    : HTTP request timeout in seconds.
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
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
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

    content: str = choices[0].get("message", {}).get("content", "")

    if not parse_json:
        return content

    stripped = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped.strip())

    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenRouter response is not valid JSON: {exc}\nRaw content: {content[:500]}") from exc
