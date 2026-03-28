"""
image_generate — Step 1 (prompt)

Renders the 360° panorama generation prompt, then calls the image generation API.

Real implementation: submits the rendered prompt to OpenRouter's image-gen API
and downloads the result to artifacts/{room_id}/panorama.jpg.

The build engine watches for panorama.jpg to appear and advances to the next
step as soon as it does — no other signalling is needed.

Stub: copies builderstubs/panorama.jpg (if present) or writes an empty placeholder.
"""

import os
import shutil
from pathlib import Path

from helpers.prompt import render

from handlers.api_provider.gemini.image import generate_image

STUB = os.getenv("STUB_ROOM_BUILDER", "false").lower() == "true"
STUBS_DIR = Path(__file__).parent.parent / "builderstubs"
STUB_IMAGE = STUBS_DIR / "panorama.jpg"

# Equirectangular panoramas need a 2:1 ratio.
# Only google/gemini-3.1-flash-image-preview supports extended aspect ratios
# (4:1, 8:1, 1:4, 1:8) via image_config — all other OpenRouter models cap at 21:9.
# seedream-4.5 ignores unsupported ratios and silently falls back to 1:1 (square).
# IMAGE_MODEL        = "gemini-3.1-flash-image-preview"   # preview — can throw 500s
IMAGE_MODEL = "gemini-2.5-flash-image"
# IMAGE_MODEL        = "black-forest-labs/flux.2-klein-4b"
# IMAGE_MODEL        = "bytedance-seed/seedream-4.5"   # NOTE: no 2:1 support, outputs square
# IMAGE_MODEL        = "sourceful/riverflow-v2-pro"
# IMAGE_MODEL        = "sourceful/riverflow-v2-fast"
IMAGE_ASPECT_RATIO = "16:9"
IMAGE_SIZE = "2K"


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    render("image_generate.txt", params, auto={}, artifacts_dir=artifacts_dir, log=log)

    out_path = artifacts_dir / "panorama.jpg"

    if out_path.exists():
        log("panorama.jpg already present — skipping generation")
        return

    if STUB:
        if STUB_IMAGE.exists():
            shutil.copy2(STUB_IMAGE, out_path)
            log(f"stub: copied builderstubs/panorama.jpg ({out_path.stat().st_size} bytes)")
        else:
            out_path.write_bytes(b"")
            log("stub: wrote empty placeholder panorama.jpg")
    else:
        prompt_text = (artifacts_dir / "src_prompts" / "image_generate.txt").read_text(encoding="utf-8")

        generate_image(
            prompt=prompt_text,
            out_path=out_path,
            log=log,
            model=IMAGE_MODEL,
            aspect_ratio=IMAGE_ASPECT_RATIO,
            image_size=IMAGE_SIZE,
        )
