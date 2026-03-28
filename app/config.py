from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
_VRESC_PROD_RAW = Path(os.getenv("VRESC_PROD_DIR", "VRESC-prod"))
VRESC_PROD_DIR = (_VRESC_PROD_RAW if _VRESC_PROD_RAW.is_absolute() else BASE_DIR / _VRESC_PROD_RAW).resolve()
VRESC_CONTENT_DIR = VRESC_PROD_DIR / "content"
VRESC_ROOMS_DIR = VRESC_CONTENT_DIR / "rooms"
VRESC_ROOM_SCHEMA_PATH = VRESC_ROOMS_DIR / "schema" / "room.schema.json"
VRESC_ROOMBUILDER_DIR = VRESC_PROD_DIR / "roombuilder"
VRESC_BUILD_SCRIPT = VRESC_ROOMBUILDER_DIR / "build.py"
VRESC_ARTIFACTS_DIR = VRESC_ROOMBUILDER_DIR / "artifacts"

UPLOADS_DIR.mkdir(exist_ok=True)


class Settings:
    BASE_DIR: Path = BASE_DIR
    VRESC_PROD_DIR: Path = VRESC_PROD_DIR
    VRESC_CONTENT_DIR: Path = VRESC_CONTENT_DIR
    VRESC_ROOMS_DIR: Path = VRESC_ROOMS_DIR
    VRESC_ROOMBUILDER_DIR: Path = VRESC_ROOMBUILDER_DIR
    VRESC_BUILD_SCRIPT: Path = VRESC_BUILD_SCRIPT
    VRESC_ARTIFACTS_DIR: Path = VRESC_ARTIFACTS_DIR

    USE_MOCKS: bool = os.getenv("USE_MOCKS", "true").lower() == "true"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    VAPI_PUBLIC_KEY: str = os.getenv("VAPI_PUBLIC_KEY", "")
    VAPI_VOICE_ID: str = os.getenv("VAPI_VOICE_ID", "xrNwYO0xeioXswMCcFNF")
    VAPI_MODEL_ID: str = os.getenv("VAPI_MODEL_ID", "gemini-2.5-flash-lite")
    IMAGE_GEN_API_KEY: str = os.getenv("IMAGE_GEN_API_KEY", "")
    ROOM_ID_PREFIX: str = os.getenv("ROOM_ID_PREFIX", "room")

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    MOCK_STEP_DELAY: float = float(os.getenv("MOCK_STEP_DELAY", "2.5"))

    ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}


settings = Settings()
