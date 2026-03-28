# Gadgets

A **gadget** is the UI panel that opens when a player clicks a hotspot in VR mode. Gadgets are implemented as ES modules served from `content/gadgets/` and loaded dynamically at runtime.

---

## How gadgets fit in the room model

```
content/rooms/<room_id>/
└── hotspots/
    └── <hs_id>/
        ├── hotspot.json      ← declares which gadget to use + all content
        └── interface.js      ← imports the gadget module and calls it
```

When a hotspot is clicked in VR:

1. `modeVR.js` imports `panel.js` → calls `buildShell(popup)` → creates the outer panel frame.
2. `modeVR.js` imports the hotspot's `interface.js` → calls `mountInterface(root, popup, onSolve, onClose)`.
3. `interface.js` imports the appropriate gadget module (e.g. `numpad.js`) and calls its builder.
4. The gadget populates the panel with its UI elements (text, buttons, inputs).

All text content comes from `hotspot.json`. Gadget modules contain no hardcoded content.

---

## Available gadgets

| Gadget | `interaction` value | File | Builder function |
|--------|---------------------|------|-----------------|
| Info panel | `"info"` | `content/gadgets/info.js` | `buildInfo(root, data, onClose)` |
| Numpad puzzle | `"numpad"` | `content/gadgets/numpad.js` | `buildNumpad(root, data, onSolve, onClose)` |
| Toggle-bank puzzle | `"toggle-bank"` | `content/gadgets/toggle-bank.js` | `buildToggleBank(root, data, onSolve, onClose)` |

---

## JSON Schemas

Each gadget has a JSON Schema in `content/gadgets/schema/` that defines the required fields for `hotspot.json → popup`:

| Schema file | Gadget |
|-------------|--------|
| `panel.schema.json` | Base fields shared by all gadgets |
| `info.schema.json` | Info gadget |
| `numpad.schema.json` | Numpad gadget |
| `toggle-bank.schema.json` | Toggle-bank gadget |

These schemas are also injected into the roombuilder's `hotspot_content` prompt so the AI knows exactly what fields to generate.

---

## The `hs:solved` event

When a puzzle is solved, `modeVR.js` dispatches a custom event on `window`:

```js
window.dispatchEvent(new CustomEvent("hs:solved", { detail: { id: "hs_entrance_door" } }));
```

The panel stays open so the player can read the success message. Any part of the application can listen to this event to track puzzle state.

---

## Further reading

- [`authoring.md`](authoring.md) — how to write gadget fields in `hotspot.json` and create a new gadget type
- [`room-compilation.md`](room-compilation.md) — everything that must be in place for a room to load correctly
