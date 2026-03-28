"""
detect_animatables — Step 2 (prompt)

Renders the animatable-elements detection prompt, then calls the vision API
with panorama.jpg to identify loopable elements in the scene.

Real implementation: pass the rendered prompt + panorama.jpg to a vision model,
receive a JSON object, validate it, write to artifacts/{room_id}/detect_animatables.json.

Stub: copies builderstubs/detect_animatables.json.
"""

import json
import os
import shutil
from pathlib import Path

from helpers.prompt import render

from handlers.api_provider.gemini.vision import chat_vision

STUB = os.getenv("STUB_ROOM_BUILDER", "false").lower() == "true"
STUBS_DIR = Path(__file__).parent.parent / "builderstubs"
STUB_JSON = STUBS_DIR / "detect_animatables.json"


def _call_vision_api(prompt_text: str, image_path: Path, out_path: Path, log) -> None:
    log(f"submitting {image_path.name} to vision API…")
    result = chat_vision(prompt_text, image_path, log=log)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"detect_animatables.json written ({out_path.stat().st_size} bytes)")


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    render("detect_animatables.txt", params, auto={}, artifacts_dir=artifacts_dir, log=log)

    out_path = artifacts_dir / "detect_animatables.json"

    if out_path.exists():
        log("detect_animatables.json already present — skipping")
        return

    if STUB:
        if STUB_JSON.exists():
            shutil.copy2(STUB_JSON, out_path)
            log(f"stub: copied builderstubs/detect_animatables.json ({out_path.stat().st_size} bytes)")
        else:
            raise FileNotFoundError(f"Stub file not found: {STUB_JSON}")
    else:
        image_path = artifacts_dir / "panorama.jpg"
        prompt_text = (artifacts_dir / "src_prompts" / "detect_animatables.txt").read_text(encoding="utf-8")
        _call_vision_api(prompt_text, image_path, out_path, log)
