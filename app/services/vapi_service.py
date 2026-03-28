from __future__ import annotations

from typing import Any

from app.config import settings

_DEFAULT_PERSONA = "The Knowledge Guide"
_DEFAULT_VOCAL_STYLE = "warm, engaging, and educational"
_DEFAULT_INTRO_MESSAGE = "Welcome, explorer. This room holds knowledge waiting to be discovered."
_DEFAULT_HINT = "Look around carefully. The answer is closer than it seems."


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}


def _as_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else fallback
    return str(value)


def generate_vapi_system_prompt(
    metadata: Any,
    vapi_config: Any,
    current_hint: str,
    final_solution: str,
) -> str:
    """Build a dynamic Vapi system prompt from current scenario state."""

    metadata_dict = _as_dict(metadata)
    vapi_config_dict = _as_dict(vapi_config)

    theme = _as_text(metadata_dict.get("theme"), "Unknown")
    story = _as_text(metadata_dict.get("story"), "Unknown")
    persona = _as_text(vapi_config_dict.get("persona"), _DEFAULT_PERSONA)
    vocal_style = _as_text(vapi_config_dict.get("vocal_style"), _DEFAULT_VOCAL_STYLE)
    intro_message = _as_text(vapi_config_dict.get("intro_message"), _DEFAULT_INTRO_MESSAGE)
    guardrails = _as_text(vapi_config_dict.get("guardrails"), "")

    system_prompt = f"""
You are the Knowledge Guide and an in-world character for an interactive, educational 360° learning experience called "Room2Learn".

# YOUR PERSONA & ROLE
You are NOT an AI assistant. You are: {persona}.
The knowledge category of this room is: {theme}.
The backstory of this room is: {story}.

# VOICE & TONE DIRECTIVES (CRITICAL)
- Speak in a {vocal_style} tone.
- Act like a real character. Use natural human speech patterns: take subtle breaths, use slight pauses (e.g., "Ah...", "Well...", "Hmm..."), and vary your pacing.
- Keep your responses VERY SHORT (1-3 sentences maximum). The user is exploring and learning, so keep them engaged without long monologues.
- Never use robotic phrases like "How can I assist you today?" or "I am an AI."

# YOUR KNOWLEDGE & CURRENT STATE
- The user is currently working on an educational challenge or asking about a specific task.
- The ONLY hint you are allowed to give them right now is based on this information: "{current_hint}".
- Do not read the hint mechanically. Weave it naturally into your persona's dialogue (e.g., if you are a historical figure, share it as a personal anecdote).

# STRICT GUARDRAILS
1. NEVER reveal the final answer directly. The final answer is: {final_solution}. If the user asks for it, refuse in-character (e.g., "True knowledge must be earned through discovery...").
2. DO NOT spoil future challenges. Only talk about the current hint provided above.
3. If the user says "Start" or "Hello", greet them EXACTLY with this message: "{intro_message}"
4. Additional guardrails from scenario config: {guardrails or "None"}

# INTERACTION STYLE
Listen carefully to the user. If they are frustrated, offer the hint gently. If they are doing well, encourage them in-character. Do not output any markdown, emojis, or formatting-only spoken words.
"""
    return system_prompt.strip()


def _extract_current_hint(scenario_context: dict[str, Any], current_step: int) -> str:
    puzzles = scenario_context.get("puzzles", [])
    if not isinstance(puzzles, list):
        return _DEFAULT_HINT
    step_index = max(1, current_step) - 1
    if step_index >= len(puzzles):
        return _DEFAULT_HINT
    puzzle = puzzles[step_index]
    if not isinstance(puzzle, dict):
        return _DEFAULT_HINT
    return _as_text(puzzle.get("hint"), _DEFAULT_HINT)


def _build_step_aware_intro(
    vapi_config: dict[str, Any],
    scenario_context: dict[str, Any],
    current_step: int,
) -> str:
    base_intro = _as_text(vapi_config.get("intro_message"), _DEFAULT_INTRO_MESSAGE)
    puzzles = scenario_context.get("puzzles", [])
    if not isinstance(puzzles, list) or not puzzles:
        return base_intro

    if current_step <= 1:
        return base_intro

    if current_step > len(puzzles):
        return "Welcome back, explorer. The final challenge remains. Enter your answer to complete the journey."

    puzzle = puzzles[current_step - 1]
    if not isinstance(puzzle, dict):
        return "Welcome back, explorer. Your next task awaits."

    puzzle_title = _as_text(puzzle.get("title"), "the next task")
    return f"Welcome back, explorer. Your next challenge awaits: {puzzle_title}."


def build_assistant_config(
    scenario_context: dict[str, Any],
    current_step: int,
    call_type: str = "intro",
) -> dict[str, Any]:
    """Assemble a Vapi inline assistant config for the web SDK."""

    _ = call_type  # Reserved for future call behavior variants.
    metadata = {
        "theme": scenario_context.get("theme", "Unknown"),
        "story": scenario_context.get("story", "Unknown"),
    }
    vapi_config = _as_dict(scenario_context.get("vapi_config", {}))
    current_hint = _extract_current_hint(scenario_context, current_step)
    final_solution = _as_text(_as_dict(scenario_context.get("final_escape", {})).get("solution"), "UNKNOWN")

    system_prompt = generate_vapi_system_prompt(
        metadata=metadata,
        vapi_config=vapi_config,
        current_hint=current_hint,
        final_solution=final_solution,
    )
    system_prompt += "\n\nThe learner is starting or resuming the voice experience."

    scenario_title = _as_text(scenario_context.get("title"), "Room2Learn")
    first_message = _build_step_aware_intro(vapi_config, scenario_context, current_step)
    first_message_mode = "assistant-speaks-first"

    name = f"R2L - {scenario_title}"[:40]

    return {
        "name": name,
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en",
        },
        "model": {
            "provider": "google",
            "model": settings.VAPI_MODEL_ID,
            "messages": [{"role": "system", "content": system_prompt}],
        },
        "voice": {
            "provider": "11labs",
            "voiceId": settings.VAPI_VOICE_ID,
        },
        "firstMessage": first_message,
        "firstMessageMode": first_message_mode,
        "maxDurationSeconds": 300,
    }
