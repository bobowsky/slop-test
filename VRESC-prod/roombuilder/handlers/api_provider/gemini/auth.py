"""
Gemini API authentication: API key resolution and shared client factory.

Reads GOOGLE_API_KEY from the project root .env and returns a configured
google.genai.Client instance ready for both Gemini and Imagen calls.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Load from the project root .env (three levels above this file's package)
_ENV_PATH = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)


def api_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        raise RuntimeError(f"GOOGLE_API_KEY is not set. Add it to {_ENV_PATH} or export it as an environment variable.")
    return key


def client() -> genai.Client:
    """Return a configured Gemini Developer API client."""
    return genai.Client(api_key=api_key())
