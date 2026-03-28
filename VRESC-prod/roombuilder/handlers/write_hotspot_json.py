"""
write_hotspot_json — Step 8 (action)

Parses hotspot_content_raw.txt and writes hotspot.json for every hotspot
into the artifacts staging area.

Reads:  artifacts/{room_id}/hotspot_content_raw.txt
Writes: artifacts/{room_id}/hotspots/{id}/hotspot.json

The raw file is the AI's full response. Two formats are accepted:

Fenced (preferred):
    ```jsonc
    // content/rooms/{room_id}/hotspots/hs_foo/hotspot.json
    { ... }
    ```

Unfenced (fallback — some models omit the fences):
    // content/rooms/{room_id}/hotspots/hs_foo/hotspot.json
    { ... }

deploy_room copies everything from artifacts/ to content/ once all steps are done.
"""

import json
import re
from pathlib import Path

# Fenced: ```jsonc ... ``` blocks with a path comment inside.
_FENCED_RE = re.compile(
    r"```jsonc?\s*\n"
    r"//\s*\S+/hotspots/(?P<id>hs_[a-z0-9_]+)/hotspot\.json\s*\n"
    r"(?P<json>\{[\s\S]*?\n\})\s*\n"
    r"```",
    re.MULTILINE,
)

# Unfenced: bare path comment followed immediately by a JSON object.
# Stops at the next path comment, fence, or end of string.
_UNFENCED_RE = re.compile(
    r"//\s*\S+/hotspots/(?P<id>hs_[a-z0-9_]+)/hotspot\.json\s*\n"
    r"(?P<json>\{[\s\S]*?\n\})",
    re.MULTILINE,
)


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    raw_path = artifacts_dir / "hotspot_content_raw.txt"
    if not raw_path.exists():
        raise FileNotFoundError(f"hotspot_content_raw.txt not found: {raw_path}")

    raw = raw_path.read_text(encoding="utf-8")
    matches = list(_FENCED_RE.finditer(raw))

    if not matches:
        # Fall back to unfenced format (model omitted code fences)
        matches = list(_UNFENCED_RE.finditer(raw))

    if not matches:
        raise RuntimeError(
            "No hotspot blocks found in hotspot_content_raw.txt.\n"
            "Expected fenced blocks:\n"
            "  ```jsonc\n"
            "  // content/rooms/{room_id}/hotspots/hs_xxx/hotspot.json\n"
            "  { ... }\n"
            "  ```\n"
            "Or unfenced:\n"
            "  // content/rooms/{room_id}/hotspots/hs_xxx/hotspot.json\n"
            "  { ... }"
        )

    out_base = artifacts_dir / "hotspots"
    written = 0

    for m in matches:
        hs_id = m.group("id")
        js_text = m.group("json").strip()

        try:
            data = json.loads(js_text)
        except json.JSONDecodeError as e:
            log(f"WARN   skipping {hs_id} — invalid JSON: {e}")
            continue

        out_dir = out_base / hs_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "hotspot.json"
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log(f"wrote  hotspots/{hs_id}/hotspot.json")
        written += 1

    log(f"total  {written} hotspot.json files written → artifacts/{room_id}/hotspots/")
