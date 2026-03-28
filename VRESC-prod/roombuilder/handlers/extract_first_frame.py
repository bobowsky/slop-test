"""
extract_first_frame.py — Extract the first frame of video.mp4 as first_frame.jpg.

Requires ffmpeg on PATH.
Input:  artifacts/{room_id}/video.mp4
Output: artifacts/{room_id}/first_frame.jpg
"""

import subprocess
from pathlib import Path


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    video = artifacts_dir / "video.mp4"
    out = artifacts_dir / "first_frame.jpg"

    if not video.exists():
        raise FileNotFoundError(f"video.mp4 not found: {video}")

    log("extracting first frame with ffmpeg…")
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-vframes",
            "1",
            "-q:v",
            "2",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    log(f"wrote  first_frame.jpg  ({out.stat().st_size // 1024} KB)")
