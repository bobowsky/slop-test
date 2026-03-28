from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from app.config import UPLOADS_DIR, VRESC_ROOMS_DIR, settings
from app.services.api_bridge import build_roombuilder_command, extract_stage_starts, strip_ansi

logger = logging.getLogger(__name__)

StageCallback = Callable[[str], Awaitable[None]]

_SUBPROCESS_TIMEOUT = 300  # 5 minutes safety net
_SENTINEL = None  # signals the reader thread is done


@dataclass(slots=True)
class RoomBuildResult:
    room_id: str
    room_dir: Path
    params_path: Path


class RoomBuilderService:
    def __init__(self) -> None:
        self._params_dir = UPLOADS_DIR / "roombuilder_params"
        self._params_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, room_id: str, image_path: Path, on_stage: StageCallback | None = None) -> RoomBuildResult:
        params_path = self._write_params(room_id, image_path)
        env = self._build_env()
        command = build_roombuilder_command(
            params_path=params_path,
            vresc_prod_dir=settings.VRESC_PROD_DIR,
            force_real_media_stages=not settings.USE_MOCKS,
        )

        logger.info("Starting roombuilder subprocess for %s", room_id)

        loop = asyncio.get_running_loop()
        stage_queue: asyncio.Queue[str | None] = asyncio.Queue()
        output_tail: deque[str] = deque(maxlen=120)

        proc = subprocess.Popen(
            command,
            cwd=str(settings.VRESC_PROD_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )

        reader = threading.Thread(
            target=self._reader_thread,
            args=(proc, loop, stage_queue, output_tail, on_stage is not None),
            daemon=True,
        )
        reader.start()

        if on_stage is not None:
            while True:
                stage_name = await stage_queue.get()
                if stage_name is _SENTINEL:
                    break
                await on_stage(stage_name)

        reader.join(timeout=_SUBPROCESS_TIMEOUT)
        return_code = proc.wait()

        logger.info("Roombuilder exited with code %d", return_code)

        if return_code != 0:
            tail = "\n".join(output_tail) if output_tail else "No output captured."
            raise RuntimeError(f"VRESC roombuilder failed with code {return_code}.\n{tail}")

        room_dir = VRESC_ROOMS_DIR / room_id
        if not room_dir.exists():
            raise RuntimeError(f"Roombuilder completed, but room output was not found at {room_dir}")

        return RoomBuildResult(
            room_id=room_id,
            room_dir=room_dir,
            params_path=params_path,
        )

    @staticmethod
    def _reader_thread(
        proc: subprocess.Popen[bytes],
        loop: asyncio.AbstractEventLoop,
        stage_queue: asyncio.Queue[str | None],
        output_tail: deque[str],
        track_stages: bool,
    ) -> None:
        seen_stages: set[str] = set()
        assert proc.stdout is not None
        try:
            for raw_line in proc.stdout:
                text = raw_line.decode("utf-8", errors="replace")
                cleaned = strip_ansi(text).strip()
                if cleaned:
                    output_tail.append(cleaned)

                if track_stages:
                    for stage_name in extract_stage_starts(text, seen_stages):
                        loop.call_soon_threadsafe(stage_queue.put_nowait, stage_name)

            proc.wait(timeout=_SUBPROCESS_TIMEOUT)
        except subprocess.TimeoutExpired:
            logger.warning("Roombuilder subprocess timed out after %ds, killing", _SUBPROCESS_TIMEOUT)
            proc.kill()
            proc.wait()
        finally:
            if track_stages:
                loop.call_soon_threadsafe(stage_queue.put_nowait, _SENTINEL)

    def _write_params(self, room_id: str, image_path: Path) -> Path:
        params_path = self._params_dir / f"{room_id}.params.json"
        payload = {
            "room_id": room_id,
            "image_path": str(image_path.resolve()),
        }
        params_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return params_path

    def _build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        if settings.OPENROUTER_API_KEY:
            env["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY
        if settings.GOOGLE_API_KEY:
            env["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        return env
