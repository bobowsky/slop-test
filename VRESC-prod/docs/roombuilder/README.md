# Roombuilder

The roombuilder is an **offline pipeline** that generates all the assets and data files needed for a VRESC room from a user-supplied description, then optionally deploys them into `content/rooms/`.

It is designed to drive **external multimodal AI APIs** — image generation, video generation, music generation, and LLM vision — automatically, based on the params supplied by the user. Each generation stage calls the appropriate external API and saves the result as an artifact.

**Current status:** The pipeline structure, stage graph, metaprompts, and all parsing/writing logic are fully implemented. The external API calls in the generation handlers are stubbed — handlers with `STUB = True` copy pre-made assets from `builderstubs/` instead of calling real APIs. Wiring the actual API clients is the remaining implementation work.

The pipeline is separate from the viewer (`app.py`) and does not run at serve time. You run it once per room, then serve the result with Flask.

---

## What it produces

For a given `room_id`, the pipeline generates:

| File | Location after deploy | Description |
|------|-----------------------|-------------|
| `panorama.jpg` | `content/rooms/<id>/` | 360° still image (fallback background) |
| `video.mp4` | `content/rooms/<id>/` | Animated 360° video (preferred background) |
| `music.mp3` | `content/rooms/<id>/` | Ambient audio track |
| `<room_id>.json` | `content/rooms/<id>/` | Hotspot layout (ids + polygons) |
| `hotspot.json` | `content/rooms/<id>/hotspots/<hs_id>/` | Gadget config per hotspot |
| `interface.js` | `content/rooms/<id>/hotspots/<hs_id>/` | Gadget bridge module per hotspot |

---

## Quick start

```bash
# Build room7 (uses stub assets — no external APIs needed)
python roombuilder/build.py roombuilder/examples/room7.params.json

# Build and copy finished assets into content/rooms/room7/
python roombuilder/build.py roombuilder/examples/room7.params.json --deploy
```

For full CLI reference see [`pipeline.md`](pipeline.md).  
For stage-by-stage details see [`stages.md`](stages.md).

---

## Directory layout

```
roombuilder/
├── build.py              # CLI entry point — run this
├── stages.yaml           # Pipeline stage graph (order, deps, outputs)
├── handlers/             # One Python module per stage
│   ├── image_generate.py
│   ├── detect_animatables.py
│   ├── music_generate.py
│   ├── video_generate.py
│   ├── extract_first_frame.py
│   ├── hotspot_grounding.py
│   ├── hotspot_content.py
│   ├── write_hotspot_json.py
│   ├── write_hotspot_interfaces.py
│   └── deploy_room.py
├── helpers/
│   ├── loaders.py        # Auto-injects schema/room data into prompts
│   └── prompt.py         # Renders metaprompt templates
├── metaprompts/          # Prompt templates for AI/human-in-the-loop steps
├── builderstubs/         # Stub assets used when STUB=True in handlers
├── examples/             # Example params files
│   └── room7.params.json
└── artifacts/            # Staging area — gitignored
    └── <room_id>/
        ├── src_prompts/  # Rendered prompts ready to paste into AI tool
        ├── panorama.jpg
        ├── video.mp4
        ├── music.mp3
        ├── detect_animatables.json
        ├── first_frame.jpg
        ├── <room_id>.json
        ├── hotspot_content_raw.txt
        └── hotspots/
            └── <hs_id>/
                ├── hotspot.json
                └── interface.js
```

---

## Stub mode

Most generation handlers have `STUB = True` near the top of their file. In stub mode the handler copies a pre-made asset from `builderstubs/` instead of calling an external API. This lets the full pipeline run end-to-end without any API keys, which is useful for development and testing the downstream stages.

To wire up real generation, set `STUB = False` in the relevant handler and implement the API call in the `NotImplementedError` branch.

---

## Prompt stages and the human-in-the-loop fallback

Stages that have a `prompt:` key in `stages.yaml` are **intended to call external AI APIs automatically** once their handlers are implemented. The metaprompt template is rendered and passed to the API; the API response is saved as the `output_artifact`.

Until a stage's API client is wired up, the pipeline falls back to human-in-the-loop mode:

1. The rendered prompt is written to `artifacts/<room_id>/src_prompts/<stage>.txt`.
2. The build display enters **WAITING** state for that stage.
3. You paste the prompt into an AI tool manually, get the output, and save it as the `output_artifact` file in `artifacts/<room_id>/`.
4. The builder detects the file (polls every 1 s) and proceeds to the next stage.

See [`pipeline.md`](pipeline.md) for the full execution model.
