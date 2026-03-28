# Roombuilder Pipeline

## Running the builder

```bash
python roombuilder/build.py <params.json> [options]
```

### Options

| Flag | Description |
|------|-------------|
| *(none)* | Run the pipeline; skip the `deploy_room` stage |
| `--deploy` | Also run `deploy_room` — copies artifacts into `content/rooms/<room_id>/` |
| `--clean` | Delete all cached artifacts for this room, then exit (no build) |
| `--clean-from <stage>` | Delete artifacts for `<stage>` and all downstream stages, then exit |
| `--cleanbuild` | Delete all artifacts, then run the full build |
| `--cleanbuild-from <stage>` | Delete artifacts from `<stage>` onward, then build from there |

The four clean flags are mutually exclusive. They only delete known `output_artifact` files listed in `stages.yaml` inside `roombuilder/artifacts/<room_id>/` — nothing outside that directory is touched.

### Examples

```bash
# Standard build (stub mode, no deploy)
python roombuilder/build.py roombuilder/examples/room7.params.json

# Build and publish to content/
python roombuilder/build.py roombuilder/examples/room7.params.json --deploy

# Regenerate everything from hotspot_content onward
python roombuilder/build.py roombuilder/examples/room7.params.json --cleanbuild-from hotspot_content

# Wipe all artifacts for room7
python roombuilder/build.py roombuilder/examples/room7.params.json --clean
```

---

## Params file

A params file is a JSON object that supplies inputs to the pipeline stages.

```json
{
  "room_id": "room7",
  "scene_description": "A quiet brutalist courtyard at golden hour...",
  "scene_summary": "Brutalist courtyard, sunset, two figures"
}
```

### Required keys

| Key | Used by stages | Description |
|-----|----------------|-------------|
| `room_id` | Most stages | Folder name; must be a valid directory name |
| `scene_description` | `image_generate`, `music_generate`, `hotspot_grounding`, `hotspot_content` | Full prose description of the scene |
| `scene_summary` | `video_generate` | Short summary for video generation prompt |

### File references

Any value can be a file path prefixed with `@` to inline the file contents:

```json
{
  "room_id": "room7",
  "scene_description": "@roombuilder/examples/room7_description.txt"
}
```

The path is resolved relative to the repository root.

---

## Execution model

### 1. Topological sort

All stages from `stages.yaml` are sorted by their `depends_on` chains. Stages with no unmet dependencies are eligible to run. The pipeline processes stages in this computed order — not top-to-bottom in the YAML file.

### 2. Stage types

**Prompt stages** (have `prompt:` in `stages.yaml`):

These stages call external multimodal AI APIs. The metaprompt template is rendered with all required variables injected, then passed to the appropriate API (image gen, video gen, music gen, or LLM with vision). The API response is saved as the `output_artifact`.

Full automated flow (when the API client is implemented in the handler):

1. Metaprompt rendered with injected variables (room params + auto-loaded schema/data).
2. Handler calls the external API with the rendered prompt (and any required input assets, e.g. an image for vision stages).
3. API response written to `artifacts/<room_id>/<output_artifact>`.
4. Stage transitions to **DONE**; downstream stages unlock.

**Human-in-the-loop fallback** (when `STUB = True` or the API call raises `NotImplementedError`):

1. The rendered prompt is written to `artifacts/<room_id>/src_prompts/<stage>.txt`.
2. The stage enters **WAITING** — the build UI shows a pulsing indicator.
3. You open the prompt file, call the appropriate AI tool manually, and save the result as the `output_artifact` file in `artifacts/<room_id>/`.
4. The builder polls every 1 second. As soon as the output file appears, the stage transitions to **DONE** and downstream stages unlock.

**Action stages** (have `action:` in `stages.yaml`):

- Run automatically by calling `handlers/<action>.run(...)`.
- If the `output_artifact` already exists in `artifacts/<room_id>/`, the stage is marked **CACHED** and skipped (no re-run).
- Stages with `output_artifact: null` (e.g. `write_hotspot_json`) always re-run.

### 3. Stage states

| State | Meaning |
|-------|---------|
| `blocked` | A dependency has not completed yet |
| `ready` | All dependencies done; waiting to execute |
| `running` | Action step currently executing |
| `waiting` | Prompt step rendered; waiting for human to drop the artifact file |
| `done` | Executed and completed this session |
| `cached` | Skipped — output artifact already existed |
| `skipped` | Pinned skip (e.g. `deploy_room` without `--deploy`) |
| `error` | Handler raised an exception |

### 4. Caching

Action stages with a non-null `output_artifact` are **cached by default**. If the artifact file exists when the stage becomes ready, the stage is immediately marked `cached` without calling its handler. Use `--clean-from <stage>` to invalidate from a specific point.

### 5. Deploy

`deploy_room` is always `skipped` unless `--deploy` is passed. When deployed, it copies from `artifacts/<room_id>/` to `content/rooms/<room_id>/`:

- `<room_id>.json` (layout)
- `hotspots/*/hotspot.json` and `hotspots/*/interface.js`
- `panorama.jpg`, `video.mp4`, `music.mp3` — only if they exist and have non-zero size

---

## Pipeline diagram

```
image_generate          ──────────────────────────────────────┐
     │                                                        │
     ├──► detect_animatables ──► video_generate               │
     │                               │                        │
     └──► music_generate             ▼                        │
                              extract_first_frame             │
                                     │                        │
                                     ▼                        │
                              hotspot_grounding ◄─────────────┘
                                     │
                                     ▼
                              hotspot_content
                                     │
                                     ▼
                              write_hotspot_json
                                     │
                                     ▼
                              write_hotspot_interfaces
                                     │
                                     ▼
                              deploy_room  (--deploy only)
```

See [`diagrams/pipeline.mmd`](diagrams/pipeline.mmd) for the Mermaid source.

---

## Handler interface

Every handler module in `roombuilder/handlers/` must expose a `run` function:

```python
def run(room_id: str, params: dict, artifacts_dir: Path, content_dir: Path, log) -> None:
    ...
```

| Parameter | Description |
|-----------|-------------|
| `room_id` | The room being built |
| `params` | Merged params dict (from params JSON + file refs resolved) |
| `artifacts_dir` | Path to `roombuilder/artifacts/<room_id>/` |
| `content_dir` | Path to `content/` (for deploy-like operations) |
| `log` | Callable — write a single-line status message to the build UI |

Raise any exception to transition the stage to `error`.

---

## Auto-injected loaders

Prompt stages can declare `auto:` keys in `stages.yaml` to inject additional context into the metaprompt without listing them in `params`. The loaders are defined in `roombuilder/helpers/loaders.py`:

| Loader key | What it injects |
|------------|-----------------|
| `room_schema` | Contents of `content/rooms/schema/room.schema.json` |
| `gadget_schemas` | All `*.schema.json` files from `content/gadgets/schema/` as JSON |
| `animatables` | Parsed `detect_animatables.json` (list form) |
| `room_json` | Contents of the built `<room_id>.json` layout file |
