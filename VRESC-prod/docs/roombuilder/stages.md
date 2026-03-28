# Pipeline Stage Reference

All stages are defined in `roombuilder/stages.yaml`. They run in dependency order, not top-to-bottom.

**Implementation status legend:**

| Badge | Meaning |
|-------|---------|
| `STUB` | Handler has `STUB = True` — uses a pre-made asset from `builderstubs/` instead of calling the external API. API wiring is pending. |
| `auto` | Runs automatically; no external API call needed. |

For stub stages, the pipeline falls back to human-in-the-loop mode: the rendered prompt is written to `src_prompts/` and the builder waits for you to drop the output file manually. See [`pipeline.md`](pipeline.md) for details.

---

## Stage 1 — `image_generate`

| Property | Value |
|----------|-------|
| Type | **prompt** |
| Depends on | *(nothing)* |
| Required params | `scene_description` |
| Output artifact | `panorama.jpg` |
| Handler | `handlers/image_generate.py` — **STUB** |
| Intended API | Text-to-image model capable of 360° equirectangular output |

Generates the 360° equirectangular panorama image from `scene_description`. The rendered prompt contains the full scene description formatted for an image generation API.

**When implemented:** handler calls the image generation API with the rendered prompt and saves the returned image as `artifacts/<room_id>/panorama.jpg`.

**Current (stub):** copies `builderstubs/panorama.jpg`. Builder enters WAITING — drop your own `panorama.jpg` into `artifacts/<room_id>/` to proceed.

---

## Stage 2 — `detect_animatables`

| Property | Value |
|----------|-------|
| Type | **prompt** |
| Depends on | `image_generate` |
| Required params | *(none)* |
| Auto-injected | *(none)* |
| Output artifact | `detect_animatables.json` |
| Handler | `handlers/detect_animatables.py` — **STUB** |
| Intended API | Multimodal LLM with vision (image input + JSON output) |

Sends `panorama.jpg` to a vision-capable LLM and asks it to identify which elements in the scene could be animated (e.g. moving leaves, flowing water, flickering lights). The result drives `video_generate`.

**When implemented:** handler calls the multimodal LLM API with the rendered prompt and `panorama.jpg` as image input, then saves the JSON response as `artifacts/<room_id>/detect_animatables.json`.

**Current (stub):** copies `builderstubs/detect_animatables.json`. Builder enters WAITING — drop a valid JSON file to proceed.

**Output format:**
```json
{
  "animatables": [
    { "element": "leaves on trees", "motion": "gentle swaying" },
    { "element": "fountain water", "motion": "flowing and splashing" }
  ]
}
```

---

## Stage 3 — `music_generate`

| Property | Value |
|----------|-------|
| Type | **prompt** |
| Depends on | `image_generate` |
| Required params | `scene_description` |
| Output artifact | `music.mp3` |
| Handler | `handlers/music_generate.py` — **STUB** |
| Intended API | Music / audio generation model (text-to-audio) |

Generates ambient background music for the room based on `scene_description`. Runs in parallel with `detect_animatables` — only requires `panorama.jpg` to exist.

**When implemented:** handler calls a music generation API with the rendered prompt and saves the returned audio as `artifacts/<room_id>/music.mp3`.

**Current (stub):** copies `builderstubs/music.mp3`. Builder enters WAITING — drop an `music.mp3` file to proceed.

---

## Stage 4 — `video_generate`

| Property | Value |
|----------|-------|
| Type | **prompt** |
| Depends on | `detect_animatables` |
| Required params | `scene_summary` |
| Auto-injected | `animatables_list` (from `detect_animatables.json`) |
| Output artifact | `video.mp4` |
| Handler | `handlers/video_generate.py` — **STUB** |
| Intended API | Image-to-video or text-to-video model capable of 360° output |

Generates a short looping 360° video based on `panorama.jpg`, animating the elements identified by `detect_animatables`. The prompt includes `scene_summary` and the list of animatable elements with their motion descriptions.

**When implemented:** handler calls a video generation API (likely image-to-video, using `panorama.jpg` as the base frame) with the rendered prompt and saves the result as `artifacts/<room_id>/video.mp4`.

**Current (stub):** copies `builderstubs/video.mp4`. Builder enters WAITING — drop a `video.mp4` file to proceed.

---

## Stage 5 — `extract_first_frame`

| Property | Value |
|----------|-------|
| Type | **action** — auto |
| Depends on | `video_generate` |
| Required params | `room_id` |
| Output artifact | `first_frame.jpg` |
| Handler | `handlers/extract_first_frame.py` |
| External tool | `ffmpeg` (must be on PATH) |

Extracts the first frame of `video.mp4` as a still image. This image is used by the hotspot grounding stage so the AI can identify precise polygon locations.

Runs automatically with `ffmpeg -i video.mp4 -frames:v 1 first_frame.jpg`.

---

## Stage 6 — `hotspot_grounding`

| Property | Value |
|----------|-------|
| Type | **prompt** |
| Depends on | `extract_first_frame` |
| Required params | `scene_description` |
| Auto-injected | `room_schema` (from `content/rooms/schema/room.schema.json`) |
| Output artifact | `<room_id>.json` |
| Handler | `handlers/hotspot_grounding.py` — **STUB** |
| Intended API | Multimodal LLM with vision (image input + structured JSON output) |

Sends `first_frame.jpg` to a vision-capable LLM with the `room.schema.json` injected into the prompt. The LLM identifies interesting objects and areas in the frame and returns a valid hotspot layout with normalized polygon coordinates.

**When implemented:** handler calls the multimodal LLM API with the rendered prompt and `first_frame.jpg` as image input, then saves the JSON response as `artifacts/<room_id>/<room_id>.json`.

**Current (stub):** copies `builderstubs/<room_id>.json`. Builder enters WAITING — drop a valid layout JSON to proceed.

**Output format** (`room.schema.json`):
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

- `id` must match pattern `^hs_[a-z0-9_]+$`
- `polygon` points are `[nx, ny]` with both values in `[0, 1]`
- Minimum 3 points per polygon; minimum 1 hotspot

---

## Stage 7 — `hotspot_content`

| Property | Value |
|----------|-------|
| Type | **prompt** |
| Depends on | `hotspot_grounding` |
| Required params | `scene_description`, `room_id` |
| Auto-injected | `gadget_schemas` (all schemas from `content/gadgets/schema/`), `room_json` (the layout file) |
| Output artifact | `hotspot_content_raw.txt` |
| Handler | `handlers/hotspot_content.py` — **STUB** |
| Intended API | LLM (text-only; JSON structured output) |

Calls an LLM to generate content for every hotspot — title, interaction type, and all gadget-specific fields. All gadget JSON schemas are injected into the prompt so the model produces structurally correct output. The room layout (`room_json`) is also injected so the model knows all hotspot IDs.

**When implemented:** handler calls the LLM API with the rendered prompt and saves the full text response as `artifacts/<room_id>/hotspot_content_raw.txt`.

**Current (stub):** copies `builderstubs/hotspot_content_raw.txt`. Builder enters WAITING — drop a valid raw text file to proceed.

**Output format** (raw text containing JSON blocks):
```
--- hs_entrance_door ---
{
  "id": "hs_entrance_door",
  "popup": {
    "interaction": "info",
    "title": "Entrance Door",
    "body": "A weathered wooden door leading into the building."
  }
}
```

---

## Stage 8 — `write_hotspot_json`

| Property | Value |
|----------|-------|
| Type | **action** — auto |
| Depends on | `hotspot_content` |
| Required params | `room_id` |
| Output artifact | `null` (always re-runs) |
| Handler | `handlers/write_hotspot_json.py` |

Parses `hotspot_content_raw.txt`, extracts each JSON block, validates the structure, and writes individual `hotspot.json` files:

```
artifacts/<room_id>/hotspots/<hs_id>/hotspot.json
```

Runs automatically.

---

## Stage 9 — `write_hotspot_interfaces`

| Property | Value |
|----------|-------|
| Type | **action** — auto |
| Depends on | `write_hotspot_json` |
| Required params | `room_id` |
| Output artifact | `null` (always re-runs) |
| Handler | `handlers/write_hotspot_interfaces.py` |

For each `hotspot.json`, reads `popup.interaction` and writes a corresponding `interface.js` from a fixed template. Supported interaction types and their templates:

| Interaction | Imports | Calls |
|-------------|---------|-------|
| `info` | `buildInfo` from `info.js` | `buildInfo(root, data, onClose)` |
| `numpad` | `buildNumpad` from `numpad.js` | `buildNumpad(root, data, onSolve, onClose)` |
| `toggle-bank` | `buildToggleBank` from `toggle-bank.js` | `buildToggleBank(root, data, onSolve, onClose)` |

Unknown `interaction` values are logged as warnings and skipped.

Runs automatically.

---

## Stage 10 — `deploy_room`

| Property | Value |
|----------|-------|
| Type | **action** — auto (`--deploy` only) |
| Depends on | `write_hotspot_interfaces`, `hotspot_grounding` |
| Required params | `room_id` |
| Output artifact | `null` |
| Handler | `handlers/deploy_room.py` |

**Skipped by default.** Pass `--deploy` to enable.

Copies the finished staging area into `content/rooms/<room_id>/`:

- `<room_id>.json` (layout)
- `hotspots/<hs_id>/hotspot.json` for all hotspots
- `hotspots/<hs_id>/interface.js` for all hotspots
- `panorama.jpg`, `video.mp4`, `music.mp3` — only if present with non-zero size

After deploy, update `ROOM_NAME` in `app.py` to `room_id` and restart Flask. 
