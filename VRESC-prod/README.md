# VRESC

A WebVR / 360° panoramic scene viewer with interactive hotspots, served by a Flask backend and rendered in-browser using A-Frame (VR mode) and a 2D canvas fallback.

---

## Overview

Each **room** is a 360° environment (still image or video) with named polygon **hotspots** overlaid on it. Clicking a hotspot opens a **gadget** — a configurable UI panel such as an info card, numpad, or toggle bank. Room content is declared in JSON; gadget logic is loaded as ES modules from `content/gadgets/`.

An optional offline **roombuilder** pipeline assists with generating and staging room content (media, hotspot definitions, interface modules) before deploying it into `content/rooms/`.

---

## Project Structure

```
VRESC/
├── app.py                        # Flask server (viewer backend)
├── templates/index.html          # Page shell (A-Frame + 2D canvas)
├── static/                       # Frontend JS/CSS
│   ├── js/app.js                 # Entry point
│   ├── js/mode2d.js              # 2D canvas mode
│   ├── js/modeVR.js              # A-Frame VR mode
│   └── js/hotspots.js            # Hotspot hit-testing and gadget dispatch
├── content/
│   ├── rooms/                    # Published room content
│   │   ├── schema/room.schema.json
│   │   └── <roomId>/
│   │       ├── <roomId>.json     # Hotspot layout (ids + polygons)
│   │       ├── panorama.jpg      # 360° still image (fallback)
│   │       ├── video.mp4         # Ambient 360° video (preferred)
│   │       ├── music.mp3         # Ambient audio
│   │       └── hotspots/
│   │           └── <hs_name>/
│   │               ├── hotspot.json    # Hotspot content and gadget config
│   │               └── interface.js   # ES module: mounts the gadget UI
│   └── gadgets/                  # Shared gadget modules + schemas
│       ├── info.js
│       ├── numpad.js
│       ├── toggle-bank.js
│       ├── panel.js
│       └── schema/               # JSON Schemas for gadget payloads
├── roombuilder/                  # Offline room generation pipeline
│   ├── build.py                  # CLI entry point
│   ├── stages.yaml               # Pipeline stage definitions
│   ├── handlers/                 # One module per pipeline stage
│   ├── helpers/                  # Prompt rendering, loaders
│   ├── metaprompts/              # LLM prompt templates
│   ├── builderstubs/             # Stub assets for offline/dry runs
│   ├── examples/                 # Example params files
│   └── artifacts/                # Per-room staging area (gitignored)
├── package.json                  # Vite dev server
├── vite.config.js                # HTTPS proxy config (port 5173 → Flask 5000)
└── requirements.txt              # Python dependencies
```

---

## Running the Viewer

> **Before starting the servers, a room must be built and deployed into `content/rooms/`.**
> The viewer will have nothing to display until at least one room is present there.
> The quickest way is a stub build — all pipeline stages run locally using pre-made stub assets
> (no external API keys or GPU required):
>
> ```bash
> python roombuilder/build.py roombuilder/examples/room7.params.json --deploy
> ```
>
> All current handlers have `STUB = True`, so this completes in seconds and populates
> `content/rooms/room7/` with placeholder media and fully-wired hotspot files.
> See [Roombuilder Pipeline](#roombuilder-pipeline) below for details.

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm

### Quick install (recommended)

Run the provided script to create a Python virtual environment, install Python and Node dependencies, and print startup instructions:

```bash
bash install.sh
```

The script checks for Python 3.10+ and Node.js 18+, creates `.venv/` if it does not exist, and installs all dependencies quietly. It does **not** start any servers — follow the printed instructions after it completes.

> **Tip:** You can override which Python binary is used: `PYTHON=python3.11 bash install.sh`

### Manual install

```bash
pip install -r requirements.txt
npm install
```

> **Note:** The roombuilder also requires `PyYAML` (`pip install pyyaml`) and `ffmpeg` on PATH.

### Start the Flask backend in activated venv

```bash
python app.py
```

Flask listens on `http://0.0.0.0:5000`. The active room defaults to `room7` (set in `app.py`).

### Start the Vite dev server (optional, for HTTPS)

```bash
npm run dev
```

Vite listens on `https://localhost:5173` and proxies `/api`, `/content`, and `/static` to Flask. Use this when WebXR (VR mode) requires a secure context.

---

## Content Model

### Room layout file — `<roomId>.json`

Declares the ordered list of hotspots with their polygon coordinates (normalized `[nx, ny]` in `[0, 1]²`):

```json
{
  "hotspots": [
    {
      "id": "hs_entrance_door",
      "polygon": [[0.42, 0.55], [0.58, 0.55], [0.58, 0.72], [0.42, 0.72]]
    }
  ]
}
```

### Hotspot content — `hotspots/<hs_name>/hotspot.json`

Defines the gadget to open when the hotspot is clicked:

```json
{
  "id": "hs_entrance_door",
  "popup": {
    "interaction": "info",
    "title": "Entrance Door",
    "body": "A weathered wooden door leading into the building."
  }
}
```

Available `interaction` types: `info`, `numpad`, `toggle-bank`.

### Hotspot interface — `hotspots/<hs_name>/interface.js`

A thin ES module that mounts the appropriate gadget:

```js
import { buildInfo } from "/content/gadgets/info.js";

export function mountInterface(container, payload) {
  buildInfo(container, payload);
}
```

### Room media

| File | Role |
|------|------|
| `video.mp4` / `video.webm` | Ambient 360° video (preferred when present) |
| `panorama.jpg` / `.png` / `.webp` | Static 360° still (fallback) |
| `music.mp3` / `.ogg` / `.wav` | Ambient background audio |

---

## Roombuilder Pipeline

The roombuilder is an offline pipeline that generates and stages room content, then deploys it into `content/rooms/`. It is driven by a **params JSON file** and a **`stages.yaml`** stage graph.

### Run the pipeline

```bash
# Build only (does not touch content/)
python roombuilder/build.py roombuilder/examples/room7.params.json

# Build and deploy into content/rooms/<room_id>/
python roombuilder/build.py roombuilder/examples/room7.params.json --deploy

# Delete all cached artifacts, then exit (no build)
python roombuilder/build.py roombuilder/examples/room7.params.json --clean

# Delete artifacts from a specific stage onward, then exit (no build)
python roombuilder/build.py roombuilder/examples/room7.params.json --clean-from hotspot_content

# Delete all cached artifacts, then run the full build
python roombuilder/build.py roombuilder/examples/room7.params.json --cleanbuild

# Delete artifacts from a specific stage onward, then build from there
python roombuilder/build.py roombuilder/examples/room7.params.json --cleanbuild-from hotspot_content
```

The `deploy_room` stage is **skipped by default**. Pass `--deploy` to copy the finished artifacts into `content/rooms/`.

All four clean flags are mutually exclusive and only delete known `output_artifact` files inside `roombuilder/artifacts/<room_id>/` — nothing outside that directory is touched.

### Params file

```json
{
  "room_id": "room7",
  "scene_description": "A quiet brutalist courtyard at golden hour...",
  "scene_summary": "Brutalist courtyard, sunset, two figures"
}
```

Parameter values can reference file contents using `"@path/from/repo/root"`.

### Pipeline stages (in order)

| Stage | Type | Output |
|-------|------|--------|
| `image_generate` | action | `panorama.jpg` |
| `detect_animatables` | prompt → action | `detect_animatables.json` |
| `music_generate` | action | `music.mp3` |
| `video_generate` | action | `video.mp4` |
| `extract_first_frame` | action | `first_frame.jpg` |
| `hotspot_grounding` | prompt → action | `hotspot_grounding.json` |
| `hotspot_content` | prompt → action | `hotspot_content_raw.txt` |
| `write_hotspot_json` | action | per-hotspot `hotspot.json` files |
| `write_hotspot_interfaces` | action | per-hotspot `interface.js` files |
| `deploy_room` | action | copies staging → `content/rooms/<room_id>/` |

Stages that have `STUB = True` in their handler use stub assets from `roombuilder/builderstubs/` instead of calling external APIs — useful for development and testing.

---

## API

| Endpoint | Description |
|----------|-------------|
| `GET /` | Serves the viewer HTML shell |
| `GET /api/scene` | Returns the active room's JSON layout |
| `GET /content/<path>` | Serves any file under `content/` (media, hotspot JSON, interface modules) |
