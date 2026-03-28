"""
music_generate — Step 3 (prompt)

Renders the ambient music generation prompt, then calls the music generation API.

Real implementation: pass the rendered prompt text to generate_audio() which
calls google/lyria-3-clip-preview via the Gemini API and writes the result to
artifacts/{room_id}/music.mp3.

Stub: copies builderstubs/music.mp3 (if present) or writes an empty placeholder.
"""

import os
import shutil
from pathlib import Path

from helpers.loaders import animatables as load_animatables
from helpers.prompt import render

from handlers.api_provider.gemini.audio import generate_audio

STUB = os.getenv("STUB_ROOM_BUILDER", "false").lower() == "true"
STUBS_DIR = Path(__file__).parent.parent / "builderstubs"
STUB_AUDIO = STUBS_DIR / "music.mp3"


def _build_scene_context(params: dict, room_id: str) -> str:
    animatables_text = load_animatables(room_id)
    return f"{params['scene_description']}\n\nAnimatable elements in this scene:\n{animatables_text}"


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    merged = dict(params)
    merged["scene_context"] = _build_scene_context(params, room_id)

    render(
        "music_generate.txt",
        merged,
        auto={},
        artifacts_dir=artifacts_dir,
        log=log,
    )

    out_path = artifacts_dir / "music.mp3"

    if out_path.exists():
        log("music.mp3 already present — skipping generation")
        return

    if STUB:
        if STUB_AUDIO.exists():
            shutil.copy2(STUB_AUDIO, out_path)
            log(f"stub: copied builderstubs/music.mp3 ({out_path.stat().st_size} bytes)")
        else:
            out_path.write_bytes(b"")
            log("stub: wrote empty placeholder music.mp3")
    else:
        prompt_text = (artifacts_dir / "src_prompts" / "music_generate.txt").read_text(encoding="utf-8")
        generate_audio(prompt_text, out_path, log=log)
