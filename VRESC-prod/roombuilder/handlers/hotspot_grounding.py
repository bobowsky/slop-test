"""
hotspot_grounding — Step 6 (prompt)

Renders the hotspot polygon identification prompt, then calls the vision API
with first_frame.jpg to identify and bound all interactive hotspots.

Real implementation: pass the rendered prompt + first_frame.jpg to a vision model,
receive a {room_id}.json layout, validate it, write to artifacts/{room_id}/{room_id}.json.

Stub: copies builderstubs/hotspot_grounding.json → artifacts/{room_id}/{room_id}.json.
"""

import json
import os
import shutil
from pathlib import Path

from helpers import loaders
from helpers.prompt import render

from handlers.api_provider.gemini.vision import chat_vision

STUB = os.getenv("STUB_ROOM_BUILDER", "false").lower() == "true"
STUBS_DIR = Path(__file__).parent.parent / "builderstubs"
STUB_JSON = STUBS_DIR / "hotspot_grounding.json"


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    auto = {"room_schema": loaders.room_schema}
    render("hotspot_grounding.txt", params, auto=auto, artifacts_dir=artifacts_dir, log=log)

    out_path = artifacts_dir / f"{room_id}.json"

    if out_path.exists():
        log(f"{room_id}.json already present — skipping")
        return

    if STUB:
        if STUB_JSON.exists():
            shutil.copy2(STUB_JSON, out_path)
            log(f"stub: copied builderstubs/hotspot_grounding.json → {room_id}.json ({out_path.stat().st_size} bytes)")
        else:
            raise FileNotFoundError(f"Stub file not found: {STUB_JSON}")
    else:
        image_path = artifacts_dir / "first_frame.jpg"
        prompt_text = (artifacts_dir / "src_prompts" / "hotspot_grounding.txt").read_text(encoding="utf-8")

        log(f"submitting {image_path.name} to vision API…")
        result = chat_vision(prompt_text, image_path, log=log)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"{room_id}.json written ({out_path.stat().st_size} bytes)")
