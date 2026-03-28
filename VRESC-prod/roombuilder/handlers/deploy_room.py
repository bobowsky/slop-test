"""
deploy_room — Step 10 (action)

Deploys the complete built room from the artifacts staging area into content/.

Copies from artifacts/{room_id}/:
  {room_id}.json          → content/rooms/{room_id}/{room_id}.json   (hotspot layout)
  hotspots/*/hotspot.json → content/rooms/{room_id}/hotspots/*/hotspot.json
  hotspots/*/interface.js → content/rooms/{room_id}/hotspots/*/interface.js
  panorama.jpg            → content/rooms/{room_id}/panorama.jpg
  video.mp4               → content/rooms/{room_id}/video.mp4
  music.mp3               → content/rooms/{room_id}/music.mp3

Media files are only copied if they are non-empty (stub placeholders are skipped).
Missing optional files are logged as warnings, not errors.
"""

import shutil
from pathlib import Path

# Media files to deploy if present and non-empty
_MEDIA = ["panorama.jpg", "video.mp4", "music.mp3"]


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    out_room = content_dir / "rooms" / room_id
    out_room.mkdir(parents=True, exist_ok=True)

    # ── scene analysis JSON (used by UI and VAPI) ──────────────────────────────
    scene_src = artifacts_dir / "scene_analyze.json"
    if scene_src.exists():
        shutil.copy2(scene_src, out_room / "scene_analyze.json")
        log("deployed  scene_analyze.json")

    # ── room layout JSON ──────────────────────────────────────────────────────
    layout_src = artifacts_dir / f"{room_id}.json"
    if layout_src.exists():
        shutil.copy2(layout_src, out_room / f"{room_id}.json")
        log(f"deployed  {room_id}.json")
    else:
        log(f"WARN   {room_id}.json not found — skipping layout")

    # ── hotspot files ─────────────────────────────────────────────────────────
    hotspots_src = artifacts_dir / "hotspots"
    if not hotspots_src.exists():
        log("WARN   artifacts/hotspots/ not found — no hotspots deployed")
    else:
        hs_count = 0
        for hs_dir in sorted(hotspots_src.iterdir()):
            if not hs_dir.is_dir():
                continue
            out_hs = out_room / "hotspots" / hs_dir.name
            out_hs.mkdir(parents=True, exist_ok=True)

            for filename in ("hotspot.json", "interface.js"):
                src = hs_dir / filename
                if src.exists():
                    shutil.copy2(src, out_hs / filename)
                else:
                    log(f"WARN   missing {hs_dir.name}/{filename}")
            hs_count += 1

        log(f"deployed  {hs_count} hotspots → content/rooms/{room_id}/hotspots/")

    # ── media files ───────────────────────────────────────────────────────────
    for filename in _MEDIA:
        src = artifacts_dir / filename
        if not src.exists():
            log(f"WARN   {filename} not found — skipping")
            continue
        if src.stat().st_size == 0:
            log(f"WARN   {filename} is empty (stub placeholder) — skipping")
            continue
        shutil.copy2(src, out_room / filename)
        log(f"deployed  {filename}  ({src.stat().st_size // 1024} KB)")

    log(f"room {room_id} deployed → content/rooms/{room_id}/")
