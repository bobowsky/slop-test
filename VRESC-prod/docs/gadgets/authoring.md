# Gadget Authoring Guide

This document explains how to write the content for each gadget type in `hotspot.json`, and how to create a new gadget type from scratch.

---

## Writing `hotspot.json`

Every `hotspot.json` file must be placed at:

```
content/rooms/<room_id>/hotspots/<hs_id>/hotspot.json
```

The top-level structure is:

```json
{
  "id": "<hs_id>",
  "popup": { ... }
}
```

- `id` must match the hotspot ID in the room layout file (`<room_id>.json`) and the folder name.
- `popup` contains all gadget fields. `buildShell()` reads `title` and `badge` from it; the gadget module reads the rest.

---

## Shared fields (all gadgets)

Defined in `content/gadgets/schema/panel.schema.json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `interaction` | string | **yes** | Gadget type: `"info"`, `"numpad"`, or `"toggle-bank"` |
| `title` | string | **yes** | Panel heading — shown in the title bar and as the main heading |
| `badge` | string | no | Small category label shown below the title bar, e.g. `"Puzzle · Infrastructure"` |

---

## Gadget: `info`

Display-only panel. Shows a title and a body of text. No interaction.

```json
{
  "id": "hs_entrance_door",
  "popup": {
    "interaction": "info",
    "title": "Entrance Door",
    "badge": "Environment",
    "body": "A weathered wooden door leading into the building. The paint is peeling in long strips."
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `interaction` | `"info"` | **yes** | |
| `title` | string | **yes** | Panel heading |
| `badge` | string | no | Category label |
| `body` | string | **yes** | Descriptive text shown in the panel body |

### `interface.js`

```js
import { buildInfo } from "/content/gadgets/info.js";

export function mountInterface(root, data, _onSolve, onClose) {
  buildInfo(root, data, onClose);
}
```

---

## Gadget: `numpad`

The player must enter a numeric code. On correct entry, `onSolve` is called.

```json
{
  "id": "hs_safe",
  "popup": {
    "interaction": "numpad",
    "title": "Wall Safe",
    "badge": "Puzzle · Security",
    "prompt": "Enter the four-digit code from the maintenance log.",
    "answer": "1957",
    "on_success": "The safe clicks open. Inside you find a key card.",
    "on_fail": "Wrong code. The panel beeps three times.",
    "hint": "Check the year on the framed certificate above the desk."
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `interaction` | `"numpad"` | **yes** | |
| `title` | string | **yes** | Panel heading |
| `badge` | string | no | Category label |
| `prompt` | string | **yes** | Instruction text shown above the numpad |
| `answer` | string | **yes** | Correct numeric answer, e.g. `"7"` or `"1957"` |
| `on_success` | string | **yes** | Message shown when the player enters the correct answer |
| `on_fail` | string | **yes** | Message shown when the player enters a wrong answer |
| `hint` | string | no | Hint text; HINT button is hidden when this key is absent |

### `interface.js`

```js
import { buildNumpad } from "/content/gadgets/numpad.js";

export function mountInterface(root, data, onSolve, onClose) {
  buildNumpad(root, data, onSolve, onClose);
}
```

---

## Gadget: `toggle-bank`

The player must set a row of switches to the correct on/off pattern. On correct pattern + CHECK press, `onSolve` is called.

```json
{
  "id": "hs_breaker_panel",
  "popup": {
    "interaction": "toggle-bank",
    "title": "Breaker Panel",
    "badge": "Puzzle · Infrastructure",
    "prompt": "Restore power to the east wing by setting the correct breakers.",
    "switches": ["TV", "WINDOW", "CABINET", "HALL"],
    "initial": [false, true, false, false],
    "target":  [true,  false, true,  true],
    "on_success": "The lights flicker on. The east wing is live.",
    "on_fail": "Nothing happens. Check the wiring diagram.",
    "hint": "The diagram on the wall shows which circuits power which rooms."
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `interaction` | `"toggle-bank"` | **yes** | |
| `title` | string | **yes** | Panel heading |
| `badge` | string | no | Category label |
| `prompt` | string | **yes** | Instruction text shown above the switches |
| `switches` | string[] (2–5 items) | **yes** | Ordered switch labels |
| `initial` | boolean[] | **yes** | Starting on/off state; must be same length as `switches` |
| `target` | boolean[] | **yes** | Correct on/off pattern; must be same length as `switches` |
| `on_success` | string | **yes** | Message shown on correct pattern |
| `on_fail` | string | **yes** | Message shown when CHECK is pressed with wrong pattern |
| `hint` | string | no | Hint text; HINT button is hidden when absent |

**Constraints:** `switches`, `initial`, and `target` must all have the same length (2–5).

### `interface.js`

```js
import { buildToggleBank } from "/content/gadgets/toggle-bank.js";

export function mountInterface(root, data, onSolve, onClose) {
  buildToggleBank(root, data, onSolve, onClose);
}
```

---

## Creating a new gadget type

To add a new `interaction` type (e.g. `"slider"`):

### 1. Write the gadget module

Create `content/gadgets/slider.js`. The module must export a builder function that populates the panel:

```js
// content/gadgets/slider.js

export function buildSlider(root, data, onSolve, onClose) {
  // root is the <a-entity> returned by buildShell()
  // data is the full popup object from hotspot.json
  // Call onSolve() when the puzzle is complete
  // Call onClose() when a close button is pressed

  // Use addText() and makeButton() from panel.js for consistent styling:
  // import { addText, makeButton } from "/content/gadgets/panel.js";
}
```

**Panel coordinate system** — content area origin at panel centre, in metres:
- Top of content area: `Y = +0.77` (below title bar)
- Bottom: `Y = −0.95`
- Left/right: `X = ±0.80`

Use `addText()` and `makeButton()` from `panel.js` for text and buttons. Use raw A-Frame elements for anything else.

### 2. Write the JSON Schema

Create `content/gadgets/schema/slider.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "slider",
  "title": "Slider gadget — popup keys (hotspot.json › popup)",
  "allOf": [{ "$ref": "panel.schema.json" }],
  "properties": {
    "interaction": { "const": "slider" },
    "prompt":      { "type": "string", "description": "..." },
    "min":         { "type": "number", "description": "..." },
    "max":         { "type": "number", "description": "..." },
    "target":      { "type": "number", "description": "..." },
    "on_success":  { "type": "string", "description": "..." },
    "on_fail":     { "type": "string", "description": "..." }
  },
  "required": ["interaction", "title", "prompt", "min", "max", "target", "on_success", "on_fail"]
}
```

The schema is automatically picked up by the roombuilder's `hotspot_content` stage via `loaders.gadget_schemas()`.

### 3. Register in the interface writer

Open `roombuilder/handlers/write_hotspot_interfaces.py` and add a template to `_TEMPLATES`:

```python
_TEMPLATES = {
    # ... existing entries ...
    "slider": """\
import {{ buildSlider }} from "/content/gadgets/slider.js";

export function mountInterface(root, data, onSolve, onClose) {{
  buildSlider(root, data, onSolve, onClose);
}}
""",
}
```

### 4. Write `hotspot.json` and `interface.js`

For manually created rooms, write `hotspot.json` using your new schema fields, and write `interface.js` using the template pattern:

```js
import { buildSlider } from "/content/gadgets/slider.js";

export function mountInterface(root, data, onSolve, onClose) {
  buildSlider(root, data, onSolve, onClose);
}
```
