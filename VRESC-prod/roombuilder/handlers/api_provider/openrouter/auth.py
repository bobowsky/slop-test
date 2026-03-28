"""
OpenRouter authentication: API key resolution and shared request headers.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load from the project root .env (three levels above this file's package)
_ENV_PATH = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)

API_BASE = "https://openrouter.ai/api/v1"


def api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError(
            f"OPENROUTER_API_KEY is not set. Add it to {_ENV_PATH} or export it as an environment variable."
        )
    return key


def headers() -> dict:
    return {
        "Authorization": f"Bearer {api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/vresc",
        "X-OpenRouter-Title": "VRESC Roombuilder",
    }
