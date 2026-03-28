"""
write_hotspot_interfaces — Step 9 (action)

Generates interface.js for every hotspot from its interaction type.

Reads:  artifacts/{room_id}/hotspots/*/hotspot.json
Writes: artifacts/{room_id}/hotspots/*/interface.js

deploy_room copies everything from artifacts/ to content/ once all steps are done.
"""

import json
from pathlib import Path

_TEMPLATES = {
    "info": """\
/**
 * {hs_id} — {title}
 * Display-only. All text comes from hotspot.json (popup.body).
 */
import {{ buildInfo }} from "/content/gadgets/info.js";

export function mountInterface(root, data, _onSolve, onClose) {{
  buildInfo(root, data, onClose);
}}
""",
    "numpad": """\
/**
 * {hs_id} — {title}
 * Player enters a numeric answer.
 * Answer and all text come from hotspot.json.
 */
import {{ buildNumpad }} from "/content/gadgets/numpad.js";

export function mountInterface(root, data, onSolve, onClose) {{
  buildNumpad(root, data, onSolve, onClose);
}}
""",
    "toggle-bank": """\
/**
 * {hs_id} — {title}
 * Player sets a switch bank to the correct pattern.
 * All labels and states come from hotspot.json.
 */
import {{ buildToggleBank }} from "/content/gadgets/toggle-bank.js";

export function mountInterface(root, data, onSolve, onClose) {{
  buildToggleBank(root, data, onSolve, onClose);
}}
""",
}


def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    hotspots_dir = artifacts_dir / "hotspots"
    if not hotspots_dir.exists():
        raise FileNotFoundError(f"Hotspots staging directory not found: {hotspots_dir}\nRun write_hotspot_json first.")

    written = 0
    for hs_dir in sorted(hotspots_dir.iterdir()):
        if not hs_dir.is_dir():
            continue
        hs_json = hs_dir / "hotspot.json"
        if not hs_json.exists():
            continue

        data = json.loads(hs_json.read_text(encoding="utf-8"))
        hs_id = data.get("id", hs_dir.name)
        interaction = data.get("popup", {}).get("interaction", "info")
        title = data.get("popup", {}).get("title", hs_id)

        template = _TEMPLATES.get(interaction)
        if template is None:
            log(f"WARN   unknown interaction '{interaction}' for {hs_id} — skipping")
            continue

        out_path = hs_dir / "interface.js"
        out_path.write_text(template.format(hs_id=hs_id, title=title), encoding="utf-8")
        log(f"wrote  hotspots/{hs_id}/interface.js  [{interaction}]")
        written += 1

    log(f"total  {written} interface.js files written → artifacts/{room_id}/hotspots/")
