# Room Compilation

"Compilation" in VRESC has two distinct meanings:

1. **Offline build** — the roombuilder pipeline that generates all room files into `roombuilder/artifacts/` and optionally deploys them into `content/rooms/`.
2. **Runtime assembly** — what Flask's `load_scene()` does on every `GET /api/scene` request to assemble the full scene payload.

This document describes what must be in place for a room to load correctly, and how both phases work.

---

## Required file structure

For a room named `<room_id>` to be served by Flask:

```
content/rooms/<room_id>/
├── <room_id>.json              ← required: hotspot layout
├── panorama.jpg                ← required: at least one media file
│   (or video.mp4, or both)
├── music.mp3                   ← optional: ambient audio
└── hotspots/
    └── <hs_id>/                ← one folder per hotspot listed in <room_id>.json
        ├── hotspot.json        ← required: gadget config
        └── interface.js        ← required: gadget bridge module
```

Flask will not crash if `hotspot.json` or `interface.js` are missing for a hotspot — it silently skips merging that hotspot's content. However, clicking the hotspot in VR will fail because `interface.js` will 404.

---

## The room layout file — `<room_id>.json`

This file lists all hotspots and their polygon shapes. It is the only required file for the room to load.

```json
{
  "hotspots": [
    {
      "id": "hs_entrance_door",
      "polygon": [[0.42, 0.55], [0.58, 0.55], [0.58, 0.72], [0.42, 0.72]]
    },
    {
      "id": "hs_safe",
      "polygon": [[0.10, 0.40], [0.25, 0.40], [0.25, 0.60], [0.10, 0.60]]
    }
  ]
}
```

### Hotspot ID rules

- Must match pattern `^hs_[a-z0-9_]+$`
- Must be unique within the room
- Determines the folder name: `hotspots/<id>/`

### Polygon format

- Each polygon is an array of `[nx, ny]` points
- `nx` and `ny` are both in `[0, 1]` (normalized equirectangular coordinates)
- `nx = 0` → left edge of the 360° image; `nx = 1` → right edge
- `ny = 0` → top; `ny = 1` → bottom
- Minimum 3 points; no maximum (but complex polygons are harder to place precisely)
- Winding order: not enforced, but consistent winding improves visual alignment with the scene

The polygon centroid is used to place the 3D hotspot disc in VR mode. The polygon boundary is used for 2D canvas hit-testing.

---

## Media files

Flask searches for media files in priority order. The first match wins:

| Kind | Search order |
|------|-------------|
| Video | `video.mp4` → `video.webm` |
| Still image | `panorama.jpg` → `panorama.png` → `panorama.jpeg` → `panorama.webp` |
| Audio | `music.mp3` → `music.ogg` → `music.wav` |

- **Video** is preferred over still image for the 360° background. If both are present, video is used.
- **Still image** is the fallback if no video is found.
- **Audio** is optional. If absent, no music is played.
- At least one of video or still image must be present for the room to render correctly.

---

## Runtime assembly — `load_scene()`

Called on every `GET /api/scene`. Returns a JSON object that the browser uses to render the room.

### Assembly steps

1. Read `content/rooms/<ROOM_NAME>/<ROOM_NAME>.json` — the hotspot layout.
2. Add `"room": "<ROOM_NAME>"` to the payload.
3. Resolve media URLs:
   - `"video": "/content/rooms/<id>/video.mp4"` (if found)
   - `"image": "/content/rooms/<id>/panorama.jpg"` (if found)
   - `"audio": "/content/rooms/<id>/music.mp3"` (if found)
4. For each hotspot in the layout, look for `hotspots/<id>/hotspot.json`:
   - If found: merge `desc` and `popup` into the hotspot object (only if not already set by the layout file).
   - If not found: hotspot appears without a gadget (clicking it shows a toast with the hotspot ID).

### Result shape

```json
{
  "room": "room7",
  "video": "/content/rooms/room7/video.mp4",
  "image": "/content/rooms/room7/panorama.jpg",
  "audio": "/content/rooms/room7/music.mp3",
  "hotspots": [
    {
      "id": "hs_entrance_door",
      "polygon": [[0.42, 0.55], [0.58, 0.55], [0.58, 0.72], [0.42, 0.72]],
      "desc": null,
      "popup": {
        "interaction": "info",
        "title": "Entrance Door",
        "body": "A weathered wooden door..."
      }
    }
  ]
}
```

---

## Switching the active room

The active room is set by `ROOM_NAME` in `app.py`:

```python
ROOM_NAME = "room7"
```

Change this value and restart Flask to serve a different room. There is no multi-room routing — only one room is served at a time.

---

## Checklist: deploying a room manually (without the builder)

Use this checklist when adding a room by hand (e.g. for testing or small rooms):

- [ ] Create `content/rooms/<room_id>/`
- [ ] Write `<room_id>.json` with at least one hotspot entry following the schema
- [ ] Add at least one media file (`panorama.jpg` or `video.mp4`)
- [ ] For each hotspot ID listed in `<room_id>.json`:
  - [ ] Create `hotspots/<hs_id>/`
  - [ ] Write `hotspot.json` with the correct `interaction` type and all required fields (see [`authoring.md`](authoring.md))
  - [ ] Write `interface.js` importing the correct gadget module and exporting `mountInterface`
- [ ] Update `ROOM_NAME` in `app.py` to `<room_id>`
- [ ] Restart Flask (`python app.py`)
- [ ] Open `http://localhost:5000` and verify the room loads

### Quick `interface.js` templates

**Info:**
```js
import { buildInfo } from "/content/gadgets/info.js";
export function mountInterface(root, data, _onSolve, onClose) {
  buildInfo(root, data, onClose);
}
```

**Numpad:**
```js
import { buildNumpad } from "/content/gadgets/numpad.js";
export function mountInterface(root, data, onSolve, onClose) {
  buildNumpad(root, data, onSolve, onClose);
}
```

**Toggle-bank:**
```js
import { buildToggleBank } from "/content/gadgets/toggle-bank.js";
export function mountInterface(root, data, onSolve, onClose) {
  buildToggleBank(root, data, onSolve, onClose);
}
```
