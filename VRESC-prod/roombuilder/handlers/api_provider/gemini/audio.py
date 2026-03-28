"""
Gemini music generation via Lyria 3 (generateContent).

Uses google.genai.Client.models.generate_content with
response_modalities=["AUDIO", "TEXT"].

Available models:
  lyria-3-clip-preview  — 30-second clips, returns MP3 directly
  lyria-3-pro-preview   — Full-length songs (controllable via prompt), MP3/WAV

The audio part arrives as inline_data.data (raw bytes, already MP3/WAV).
No local transcoding step is needed unlike the OpenRouter pcm16 path.

References:
  https://ai.google.dev/gemini-api/docs/music-generation
"""

import base64
from pathlib import Path

from google.genai import types

from .auth import client

DEFAULT_AUDIO_MODEL = "lyria-3-clip-preview"
DEFAULT_AUDIO_FORMAT = "mp3"

# Lyria 3 always outputs in MP3 (Clip) or MP3/WAV (Pro).
# The `voice` parameter has no meaning for music models;
# it is accepted for interface parity only.
_UNSUPPORTED_VOICE_NOTE = "gemini: 'voice' parameter is not applicable to Lyria music models and will be ignored."


def generate_audio(
    prompt: str,
    out_path: Path,
    log=print,
    *,
    model: str = DEFAULT_AUDIO_MODEL,
    voice: str = "",
    audio_format: str = DEFAULT_AUDIO_FORMAT,
    timeout: int = 180,
) -> None:
    """
    Generate music/audio from a text prompt via Lyria 3 and write to *out_path*.

    The Lyria 3 Clip model always produces a 30-second MP3 clip.
    The Lyria 3 Pro model generates full-length songs; influence duration by
    including it in the prompt (e.g. "create a 2-minute ambient track").

    Parameters
    ----------
    prompt       : Text prompt describing the music (genre, instruments, BPM,
                   key, mood, structure tags, custom lyrics, timestamps…).
    out_path     : Destination file path (.mp3 or .wav recommended).
    log          : Callable used for progress messages.
    model        : Lyria model identifier ("lyria-3-clip-preview" or
                   "lyria-3-pro-preview").
    voice        : Not used for Lyria models (accepted for interface parity).
    audio_format : Informational; Lyria output format is controlled by the
                   model itself (MP3 for Clip, MP3/WAV for Pro).
    timeout      : Unused for the SDK path (included for interface parity).

    Raises
    ------
    RuntimeError on API errors or when no audio part is returned.
    """
    if voice:
        log(_UNSUPPORTED_VOICE_NOTE)

    log(f"gemini: generate_content  model={model}  (music)")

    with client() as c:
        response = c.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO", "TEXT"],
            ),
        )

    audio_bytes: bytes | None = None
    lyrics_parts: list[str] = []

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None and audio_bytes is None:
            audio_bytes = part.inline_data.data
        elif part.text is not None:
            lyrics_parts.append(part.text)

    if audio_bytes is None:
        raise RuntimeError(
            f"Gemini returned no audio part. Check that the model supports audio generation.\nResponse: {response}"
        )

    if isinstance(audio_bytes, str):
        audio_bytes = base64.b64decode(audio_bytes)

    out_path.write_bytes(audio_bytes)
    log(f"gemini: audio saved → {out_path} ({len(audio_bytes):,} bytes)")

    if lyrics_parts:
        lyrics_text = "\n".join(lyrics_parts)
        lyrics_path = out_path.with_suffix(".lyrics.txt")
        lyrics_path.write_text(lyrics_text, encoding="utf-8")
        log(f"gemini: lyrics saved → {lyrics_path}")
