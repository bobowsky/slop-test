"""
video_generate — Step 4 (prompt)

Renders the animated 360° video generation prompt, injecting the
animatables list from the previous step, then calls the Gemini Veo 3.1 API.

Real implementation: submits prompt + panorama.jpg (as first frame) to
Veo 3.1 via the Gemini Developer API, polls until the long-running operation
completes, then saves the result to artifacts/{room_id}/video.mp4.

Stub: copies builderstubs/video.mp4 (if present) or writes an empty placeholder.
"""

import os
import shutil
from pathlib import Path

from helpers import loaders
from helpers.prompt import render

from handlers.api_provider.gemini.video import generate_video

STUB = os.getenv("STUB_ROOM_BUILDER", "false").lower() == "true"
STUBS_DIR = Path(__file__).parent.parent / "builderstubs"
STUB_VIDEO = STUBS_DIR / "video.mp4"

VIDEO_MODEL = "veo-3.1-generate-preview"
VIDEO_ASPECT = "16:9"
VIDEO_DURATION = 8  # seconds (Veo 3.1 generates 8-second clips)
VIDEO_TIMEOUT = 600  # seconds to wait for the operation


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    auto = {"animatables_list": loaders.animatables}
    render("video_generate.txt", params, auto=auto, artifacts_dir=artifacts_dir, log=log)

    out_path = artifacts_dir / "video.mp4"

    if out_path.exists():
        log("video.mp4 already present — skipping generation")
        return

    if STUB:
        if STUB_VIDEO.exists():
            shutil.copy2(STUB_VIDEO, out_path)
            log(f"stub: copied builderstubs/video.mp4 ({out_path.stat().st_size} bytes)")
        else:
            out_path.write_bytes(b"")
            log("stub: wrote empty placeholder video.mp4")
    else:
        image_path = artifacts_dir / "panorama.jpg"
        prompt_text = (artifacts_dir / "src_prompts" / "video_generate.txt").read_text(encoding="utf-8")

        generate_video(
            prompt=prompt_text,
            out_path=out_path,
            log=log,
            image_path=image_path if image_path.exists() else None,
            model=VIDEO_MODEL,
            aspect_ratio=VIDEO_ASPECT,
            duration_seconds=VIDEO_DURATION,
            timeout=VIDEO_TIMEOUT,
        )
