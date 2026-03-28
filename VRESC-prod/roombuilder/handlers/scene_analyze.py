"""
scene_analyze — Step 0 (prompt)

Analyses the uploaded room photo using a vision model and produces a structured
JSON with scene_description and scene_summary.  These values are merged into
the build params so that all downstream stages can use them in their metaprompts.

Real implementation: sends the image to Gemini vision and writes the parsed
JSON result to artifacts/{room_id}/scene_analyze.json.

Stub: copies builderstubs/scene_analyze.json.
"""

import json
import os
import shutil
from pathlib import Path

from helpers.prompt import render

from handlers.api_provider.gemini.vision import chat_vision

STUB = os.getenv("STUB_ROOM_BUILDER", "false").lower() == "true"
STUBS_DIR = Path(__file__).parent.parent / "builderstubs"
STUB_JSON = STUBS_DIR / "scene_analyze.json"


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    render("scene_analyze.txt", params, auto={}, artifacts_dir=artifacts_dir, log=log)

    out_path = artifacts_dir / "scene_analyze.json"

    if out_path.exists():
        log("scene_analyze.json already present — skipping")
        return

    if STUB:
        if STUB_JSON.exists():
            shutil.copy2(STUB_JSON, out_path)
            log(f"stub: copied builderstubs/scene_analyze.json ({out_path.stat().st_size} bytes)")
        else:
            raise FileNotFoundError(f"Stub file not found: {STUB_JSON}")
    else:
        image_path = Path(params["image_path"])
        if not image_path.exists():
            raise FileNotFoundError(f"Uploaded image not found: {image_path}")

        prompt_text = (artifacts_dir / "src_prompts" / "scene_analyze.txt").read_text(encoding="utf-8")

        log(f"submitting {image_path.name} to vision API…")
        result = chat_vision(prompt_text, image_path, log=log)

        if not isinstance(result, dict):
            raise RuntimeError(f"Scene analysis returned non-dict: {type(result)}")

        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"scene_analyze.json written ({out_path.stat().st_size} bytes)")
