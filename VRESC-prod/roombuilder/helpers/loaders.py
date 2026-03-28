"""
loaders.py — Auto-variable loaders for metaprompt rendering.

Each function signature: (room_id: str) -> str
Referenced by name in stages.yaml under each step's `auto:` block.
"""

import json
from pathlib import Path

# Repo root is two levels up from this file: roombuilder/helpers/ → roombuilder/ → repo root
ROOT = Path(__file__).parent.parent.parent


def room_schema(_room_id: str) -> str:
    path = ROOT / "content" / "rooms" / "schema" / "room.schema.json"
    return json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2)


def gadget_schemas(_room_id: str) -> str:
    schemas = {}
    for f in sorted((ROOT / "content" / "gadgets" / "schema").glob("*.schema.json")):
        schemas[f.stem.replace(".schema", "")] = json.loads(f.read_text(encoding="utf-8"))
    return json.dumps(schemas, indent=2)


def animatables(room_id: str) -> str:
    path = ROOT / "roombuilder" / "artifacts" / room_id / "detect_animatables.json"
    if not path.exists():
        raise FileNotFoundError(f"detect_animatables artifact not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def room_json(room_id: str) -> str:
    path = ROOT / "roombuilder" / "artifacts" / room_id / f"{room_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Room JSON artifact not found: {path}")
    return path.read_text(encoding="utf-8").strip()
