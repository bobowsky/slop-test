from __future__ import annotations

import re
import sys
from pathlib import Path

ROOBUILDER_STAGES: tuple[str, ...] = (
    "scene_analyze",
    "image_generate",
    "detect_animatables",
    "music_generate",
    "video_generate",
    "extract_first_frame",
    "hotspot_grounding",
    "hotspot_content",
    "write_hotspot_json",
    "write_hotspot_interfaces",
    "deploy_room",
)

_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
_STAGE_RE = re.compile(
    r"\b(" + "|".join(ROOBUILDER_STAGES) + r")\b.*\b(running|waiting artifact|done|cached|stub|error)\b",
    flags=re.IGNORECASE,
)


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def build_roombuilder_command(
    *,
    params_path: Path,
    vresc_prod_dir: Path,
    force_real_media_stages: bool,
) -> list[str]:
    """Build a subprocess command that runs VRESC's pipeline untouched."""

    if force_real_media_stages:
        # Runtime-only override: keep VRESC source files unchanged while enabling
        # real API execution for all prompt handlers.
        bootstrap = (
            "import sys\n"
            "import shutil\n"
            "from pathlib import Path\n"
            "params_path = Path(sys.argv[1]).resolve()\n"
            "vresc_dir = Path(sys.argv[2]).resolve()\n"
            "roombuilder_dir = vresc_dir / 'roombuilder'\n"
            "sys.path.insert(0, str(roombuilder_dir))\n"
            "import handlers.scene_analyze as scene_analyze\n"
            "import handlers.image_generate as image_generate\n"
            "import handlers.detect_animatables as detect_animatables\n"
            "import handlers.music_generate as music_generate\n"
            "import handlers.video_generate as video_generate\n"
            "import handlers.hotspot_grounding as hotspot_grounding\n"
            "import handlers.hotspot_content as hotspot_content\n"
            "import handlers.extract_first_frame as extract_first_frame\n"
            "scene_analyze.STUB = False\n"
            "image_generate.STUB = False\n"
            "detect_animatables.STUB = False\n"
            "music_generate.STUB = False\n"
            "video_generate.STUB = False\n"
            "hotspot_grounding.STUB = False\n"
            "hotspot_content.STUB = False\n"
            "_orig_extract = extract_first_frame.run\n"
            "def _patched_extract(room_id, params, artifacts_dir, content_dir, log):\n"
            "    try:\n"
            "        _orig_extract(room_id, params, artifacts_dir, content_dir, log)\n"
            "    except Exception as exc:\n"
            "        pano = artifacts_dir / 'panorama.jpg'\n"
            "        out = artifacts_dir / 'first_frame.jpg'\n"
            "        if pano.exists():\n"
            "            shutil.copy2(pano, out)\n"
            "            log(f'fallback: first_frame from panorama ({exc})')\n"
            "        else:\n"
            "            raise\n"
            "extract_first_frame.run = _patched_extract\n"
            "import build\n"
            "build.run_build(params_path, deploy=True, clean_all=True, clean_from=None, build=True)\n"
        )
    else:
        # Fully mocked pipeline mode: force all prompt stages to use stubs.
        bootstrap = (
            "import sys\n"
            "import shutil\n"
            "from pathlib import Path\n"
            "params_path = Path(sys.argv[1]).resolve()\n"
            "vresc_dir = Path(sys.argv[2]).resolve()\n"
            "roombuilder_dir = vresc_dir / 'roombuilder'\n"
            "sys.path.insert(0, str(roombuilder_dir))\n"
            "import handlers.scene_analyze as scene_analyze\n"
            "import handlers.image_generate as image_generate\n"
            "import handlers.detect_animatables as detect_animatables\n"
            "import handlers.music_generate as music_generate\n"
            "import handlers.video_generate as video_generate\n"
            "import handlers.hotspot_grounding as hotspot_grounding\n"
            "import handlers.hotspot_content as hotspot_content\n"
            "import handlers.extract_first_frame as extract_first_frame\n"
            "scene_analyze.STUB = True\n"
            "image_generate.STUB = True\n"
            "detect_animatables.STUB = True\n"
            "music_generate.STUB = True\n"
            "video_generate.STUB = True\n"
            "hotspot_grounding.STUB = True\n"
            "hotspot_content.STUB = True\n"
            "_orig_extract = extract_first_frame.run\n"
            "def _patched_extract(room_id, params, artifacts_dir, content_dir, log):\n"
            "    try:\n"
            "        _orig_extract(room_id, params, artifacts_dir, content_dir, log)\n"
            "    except Exception as exc:\n"
            "        pano = artifacts_dir / 'panorama.jpg'\n"
            "        out = artifacts_dir / 'first_frame.jpg'\n"
            "        if pano.exists():\n"
            "            shutil.copy2(pano, out)\n"
            "            log(f'fallback: first_frame from panorama ({exc})')\n"
            "        else:\n"
            "            raise\n"
            "extract_first_frame.run = _patched_extract\n"
            "import build\n"
            "build.run_build(params_path, deploy=True, clean_all=True, clean_from=None, build=True)\n"
        )

    return [
        sys.executable,
        "-c",
        bootstrap,
        str(params_path),
        str(vresc_prod_dir),
    ]


def extract_stage_starts(raw_line: str, seen_stages: set[str]) -> list[str]:
    """
    Parse a roombuilder output line and return newly started stages.

    A stage is considered "started" when it first appears in a running/waiting
    or terminal state line in the live dashboard output.
    """

    clean = strip_ansi(raw_line)
    matches = _STAGE_RE.finditer(clean)
    found: list[str] = []
    for match in matches:
        stage_name = match.group(1).strip()
        if stage_name in seen_stages:
            continue
        seen_stages.add(stage_name)
        found.append(stage_name)
    return found
