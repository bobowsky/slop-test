"""
OpenRouter audio generation via the chat/completions endpoint (streaming pcm16).

The OpenAI-compatible audio route on OpenRouter only supports pcm16 when
streaming.  Raw PCM is received, then transcoded locally via pydub.
"""

import base64
import json
from pathlib import Path

import requests

from .auth import API_BASE, headers

DEFAULT_AUDIO_MODEL = "openai/gpt-audio-mini"
DEFAULT_AUDIO_VOICE = "alloy"
DEFAULT_AUDIO_FORMAT = "mp3"

# OpenRouter / OpenAI only support pcm16 in streaming mode; we transcode.
_STREAM_AUDIO_FORMAT = "pcm16"
_PCM16_SAMPLE_RATE = 24000
_PCM16_CHANNELS = 1
_PCM16_SAMPLE_WIDTH = 2  # bytes (16-bit)


def generate_audio(
    prompt: str,
    out_path: Path,
    log=print,
    *,
    model: str = DEFAULT_AUDIO_MODEL,
    voice: str = DEFAULT_AUDIO_VOICE,
    audio_format: str = DEFAULT_AUDIO_FORMAT,
    timeout: int = 180,
) -> None:
    """
    Generate audio from a text prompt via OpenRouter and write it to *out_path*.

    Uses the chat/completions endpoint with modalities=["text","audio"].
    Audio arrives as base64-encoded pcm16 chunks over SSE and is transcoded
    to the requested *audio_format* using pydub.

    Parameters
    ----------
    prompt       : Text prompt for the audio model.
    out_path     : Destination file path (extension should match audio_format).
    log          : Callable used for progress messages.
    model        : OpenRouter model identifier.
    voice        : Voice to use (e.g. "alloy", "echo", "fable", "onyx", "nova").
    audio_format : Audio container format ("mp3", "wav", "flac", "opus", "aac").
    timeout      : HTTP request timeout in seconds.

    Raises
    ------
    RuntimeError on API errors or when no audio data is returned.
    """
    payload: dict = {
        "model": model,
        "modalities": ["text", "audio"],
        "audio": {"voice": voice, "format": _STREAM_AUDIO_FORMAT},
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }

    log(f"openrouter: POST {API_BASE}/chat/completions  model={model}  voice={voice}  stream=pcm16→{audio_format}")
    resp = requests.post(
        f"{API_BASE}/chat/completions",
        headers=headers(),
        json=payload,
        timeout=timeout,
        stream=True,
    )

    if not resp.ok:
        raise RuntimeError(f"OpenRouter API error {resp.status_code}: {resp.text[:500]}")

    audio_b64_chunks: list[str] = []

    for raw_line in resp.iter_lines():
        if isinstance(raw_line, bytes):
            raw_line = raw_line.decode("utf-8")
        if not raw_line.startswith("data:"):
            continue
        payload_str = raw_line[len("data:") :].strip()
        if payload_str == "[DONE]":
            break
        try:
            chunk = json.loads(payload_str)
        except json.JSONDecodeError:
            continue
        if "error" in chunk:
            raise RuntimeError(f"OpenRouter stream error: {chunk['error']}")
        delta = chunk.get("choices", [{}])[0].get("delta", {})
        chunk_b64 = (delta.get("audio") or {}).get("data", "")
        if chunk_b64:
            audio_b64_chunks.append(chunk_b64)

    if not audio_b64_chunks:
        raise RuntimeError(
            "OpenRouter stream finished with no audio data. "
            "Check that the model supports audio output and that "
            "`modalities` includes 'audio'."
        )

    pcm_bytes = base64.b64decode("".join(audio_b64_chunks))
    log(f"openrouter: received {len(pcm_bytes):,} bytes pcm16 — transcoding to {audio_format}…")

    try:
        from pydub import AudioSegment  # optional dependency
    except ImportError as exc:
        raise RuntimeError("pydub is required to transcode pcm16 → audio. Install it with: pip install pydub") from exc

    segment = AudioSegment(
        data=pcm_bytes,
        sample_width=_PCM16_SAMPLE_WIDTH,
        frame_rate=_PCM16_SAMPLE_RATE,
        channels=_PCM16_CHANNELS,
    )
    segment.export(str(out_path), format=audio_format)
    log(f"openrouter: audio saved → {out_path} ({out_path.stat().st_size:,} bytes)")
