# Application Modules

## Module Map

```
VRESC/
├── app.py                    ← Python: Flask backend
├── templates/index.html      ← HTML shell loaded once
└── static/js/
    ├── app.js                ← Entry point: fetch scene, mode switching
    ├── mode2d.js             ← 2D canvas viewer
    ├── modeVR.js             ← A-Frame VR viewer + panel lifecycle
    └── hotspots.js           ← Shared geometry utilities

content/gadgets/              ← Gadget ES modules (served by Flask)
    ├── panel.js              ← Shell builder (shared by all gadgets)
    ├── info.js               ← Info gadget
    ├── numpad.js             ← Numpad puzzle gadget
    └── toggle-bank.js        ← Switch-bank puzzle gadget

content/rooms/<id>/hotspots/<hs_id>/
    └── interface.js          ← Per-hotspot bridge module
```

---

## Backend — `app.py`

**Role:** Assembles and serves the scene payload; serves all content files.

### `load_scene()`

Called on every `GET /api/scene` request. Builds the full scene object that the browser uses:

1. Reads `content/rooms/<ROOM_NAME>/<ROOM_NAME>.json` — the hotspot layout (ids + polygons).
2. Appends `"room": "<ROOM_NAME>"` to the payload.
3. Scans the room directory for media files in priority order:
   - `video`: `video.mp4` → `video.webm`
   - `image`: `panorama.jpg` → `.png` → `.jpeg` → `.webp`
   - `audio`: `music.mp3` → `.ogg` → `.wav`
4. For each hotspot entry, reads `hotspots/<id>/hotspot.json` and merges:
   - `desc` (optional description)
   - `popup` (gadget config — only if not already set in the layout file)

### Routes

| Route | Handler | Description |
|-------|---------|-------------|
| `GET /` | `index()` | Renders `templates/index.html` |
| `GET /api/scene` | `api_scene()` | Returns `load_scene()` as JSON |
| `GET /content/<path>` | `content_file()` | Serves any file under `content/` |

### Configuration

`ROOM_NAME` is a module-level constant in `app.py`. Change it to switch which room is served:

```python
ROOM_NAME = "room7"
```

---

## Frontend Entry — `static/js/app.js`

**Role:** Bootstraps the application; owns mode switching.

1. On `DOMContentLoaded`: calls `fetch("/api/scene")` once, stores `sceneData`.
2. Wires mode buttons (`#btn-2d`, `#btn-vr`).
3. On mode switch: calls `destroy*()` on the outgoing mode, then `init*()` on the incoming mode, passing `sceneData`.

**Starts in 2D mode** by default.

---

## 2D Viewer — `static/js/mode2d.js`

**Role:** Renders the panorama as a flat canvas with clickable polygon overlays.

| Function | Description |
|----------|-------------|
| `init2D(canvas, data)` | Loads video or image; starts render loop; attaches mouse events |
| `destroy2D()` | Cancels animation frame; pauses video; removes listeners |

**Rendering:** Each frame draws the full video/image stretched to canvas size, then draws each hotspot polygon on top (yellow outline, semi-transparent fill, label at centroid).

**Interaction:** `mousemove` → `pointInPolygon` hit-test → hover highlight. `click` → `showToast(title)`. **No gadgets are opened in 2D mode.**

**Coordinate system:** Polygon `[nx, ny]` values in `[0,1]` are multiplied by canvas pixel size on each render.

---

## VR Viewer — `static/js/modeVR.js`

**Role:** Builds an A-Frame scene; places hotspot discs in 3D space; manages panel lifecycle.

### Scene Construction (`buildSceneHTML`)

- Creates a full `<a-scene>` with:
  - `<a-videosphere>` or `<a-sky>` for the 360° background
  - One `<a-entity>` per hotspot (see below)
  - Camera with mouse cursor raycaster
  - Left/right laser controllers for Meta Quest / WebXR

### Hotspot Disc Entity (`buildHotspotEntity`)

Each hotspot polygon is converted to a 3D position via `polygonTo3D()`:
- Centroid of polygon → `(nx, ny)` → yaw/pitch (degrees) → `(x, y, z)` on a sphere of radius 9.5 m.

The entity consists of:
- A torus ring (glow effect) — carries `class="hotspot-hit"` for raycaster
- An inner circle with a pulsing opacity animation
- An `<a-text>` label below the disc

Disc color indicates type:
- **Gold** `#ffd700` — `info` (display-only)
- **Green** `#7ecf3a` — `numpad`, `toggle-bank` (interactive puzzle)

### Panel Lifecycle (`openPanel` / `closePanel`)

On hotspot click:
1. `closePanel()` — removes any open panel from the DOM.
2. Dynamically imports `panel.js` → calls `buildShell(popup)` to create the outer frame.
3. Dynamically imports the hotspot's `interface.js` → calls `mountInterface(root, popup, onSolve, closePanel)`.
4. Appends the panel to `[camera]` so it follows the player's view.
5. On puzzle solve: dispatches `CustomEvent("hs:solved", { detail: { id } })` on `window`.

### Audio

- **Video** (`video.mp4`): always muted. Ambient sound comes from the music track.
- **Music** (`music.mp3`): played via `new Audio(src)`, looped at volume 0.55. Paused and cleaned up on `destroyVR()`.

---

## Geometry Utilities — `static/js/hotspots.js`

Shared by both 2D and VR modes.

| Export | Description |
|--------|-------------|
| `centroid(polygon)` | Arithmetic mean of polygon vertices |
| `pointInPolygon(px, py, polygon)` | Ray-casting hit test |
| `normalizedToYawPitch(nx, ny)` | `[0,1]²` → yaw/pitch in degrees |
| `yawPitchToPosition(yaw, pitch, r)` | Spherical → Cartesian (A-Frame Y-up) |
| `polygonTo3D(polygon, r)` | Full pipeline: polygon → 3D position + angles |
| `showToast(message)` | Brief overlay notification |

**Coordinate conventions:**
- `nx=0` → yaw `−180°` (left edge of equirectangular image)
- `nx=1` → yaw `+180°` (right edge)
- `ny=0` → pitch `+90°` (top)
- `ny=1` → pitch `−90°` (bottom)

---

## Panel Shell — `content/gadgets/panel.js`

**Role:** Shared A-Frame geometry builder. Creates the outer chrome of every popup panel. Contains no interaction logic.

| Export | Description |
|--------|-------------|
| `buildShell(popup)` | Creates the panel root entity: border plane, background, title bar, badge (optional), heading |
| `addText(parent, value, position, opts)` | Creates an `<a-text>` element and appends it |
| `makeButton(label, position, w, h, bgColor, textColor)` | Creates a flat `<a-plane>` button with a text label and hover highlight |

**Panel coordinate system** (metres, origin at panel centre):
- Top edge: `Y = +0.95`
- Title bar bottom / content start: `Y = +0.77`
- Bottom edge: `Y = −0.95`
- Left/right edges: `X = ±0.80`

---

## Gadget Modules — `content/gadgets/*.js`

Each gadget exports a single builder function that populates the panel shell:

| Module | Export | Interaction type |
|--------|--------|-----------------|
| `info.js` | `buildInfo(root, data, onClose)` | `"info"` |
| `numpad.js` | `buildNumpad(root, data, onSolve, onClose)` | `"numpad"` |
| `toggle-bank.js` | `buildToggleBank(root, data, onSolve, onClose)` | `"toggle-bank"` |

All data comes from `hotspot.json → popup`. No hardcoded content in gadget modules.

---

## Per-Hotspot Bridge — `interface.js`

Each hotspot folder contains an `interface.js` generated by the roombuilder. It is a thin adapter that imports the appropriate gadget module and calls it:

```js
import { buildNumpad } from "/content/gadgets/numpad.js";

export function mountInterface(root, data, onSolve, onClose) {
  buildNumpad(root, data, onSolve, onClose);
}
```

**Contract:** Must export `mountInterface(root, data, onSolve, onClose)`.

- `root` — the panel root `<a-entity>` returned by `buildShell()`
- `data` — the full `popup` object from `hotspot.json`
- `onSolve` — call when the puzzle is solved; dispatches `hs:solved` event
- `onClose` — call to close the panel

---

## Module Communication Diagram

```
app.js
  │
  ├─ fetch /api/scene ──────────────────────────────► Flask app.py
  │                                                      │
  │  sceneData                                           ▼ merges layout + hotspot.json
  │
  ├─ init2D(canvas, sceneData) ────────────────────► mode2d.js
  │                                                      │
  │                                              imports hotspots.js
  │                                              (pointInPolygon, showToast)
  │
  └─ initVR(container, sceneData) ─────────────────► modeVR.js
                                                         │
                                                 imports hotspots.js
                                                 (polygonTo3D, showToast)
                                                         │
                                          on hotspot click:
                                                         │
                                              dynamic import panel.js
                                              → buildShell(popup) → root entity
                                                         │
                                              dynamic import interface.js
                                              → mountInterface(root, popup, onSolve, onClose)
                                                         │
                                              interface.js imports gadget module
                                              (info.js / numpad.js / toggle-bank.js)
                                                         │
                                              onSolve() → window.dispatchEvent("hs:solved")
```
