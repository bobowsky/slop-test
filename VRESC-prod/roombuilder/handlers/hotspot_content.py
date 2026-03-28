"""
hotspot_content — Step 7 (prompt)

Renders the hotspot content generation prompt, injecting gadget schemas
and the room layout JSON from previous steps, then calls the language model API.

Real implementation: submit the rendered prompt to the LLM API, receive the full
response text, write it to artifacts/{room_id}/hotspot_content_raw.txt.

Stub: copies builderstubs/hotspot_content_raw.txt (if present).
"""

import os
import shutil
from pathlib import Path

from helpers import loaders
from helpers.prompt import render

from handlers.api_provider.gemini.chat import chat_text

STUB = os.getenv("STUB_ROOM_BUILDER", "false").lower() == "true"
STUBS_DIR = Path(__file__).parent.parent / "builderstubs"
STUB_RAW = STUBS_DIR / "hotspot_content_raw.txt"


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    auto = {
        "gadget_schemas": loaders.gadget_schemas,
        "room_json": loaders.room_json,
    }
    render("hotspot_content.txt", params, auto=auto, artifacts_dir=artifacts_dir, log=log)

    out_path = artifacts_dir / "hotspot_content_raw.txt"

    if out_path.exists():
        log("hotspot_content_raw.txt already present — skipping")
        return

    if STUB:
        if STUB_RAW.exists():
            shutil.copy2(STUB_RAW, out_path)
            log(f"stub: copied builderstubs/hotspot_content_raw.txt ({out_path.stat().st_size} bytes)")
        else:
            raise FileNotFoundError(f"Stub file not found: {STUB_RAW}")
    else:
        prompt_text = (artifacts_dir / "src_prompts" / "hotspot_content.txt").read_text(encoding="utf-8")

        log("submitting to LLM API…")
        result = chat_text(prompt_text, log=log, parse_json=False)
        out_path.write_text(result, encoding="utf-8")
        log(f"hotspot_content_raw.txt written ({out_path.stat().st_size} bytes)")
