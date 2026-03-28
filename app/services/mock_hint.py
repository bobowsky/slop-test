"""Mock implementation of HintProvider.

Replaces: LLM call for contextual hint generation (e.g. GPT-4o, Gemini)
Ignores:  Actual scenario context and user question content
Returns:  Canned hints mapped to challenge step numbers
Expected real latency: 1-3 seconds
"""

from __future__ import annotations

from app.models.schemas import HintResponse
from app.services.interfaces import HintProvider

_HINTS: dict[int, HintResponse] = {
    1: HintResponse(
        hint="Look carefully at the engravings on the Medieval Chalice. The coat of arms reveals the era of Poland's baptism.",
        voice_friendly="The chalice bears a royal crest. Think about when Poland was first baptized as a Christian nation.",
    ),
    2: HintResponse(
        hint="The Astrolabe points to the century when higher learning began in Europe. Think Bologna, 1088.",
        voice_friendly="The first European university was founded in Bologna. What century was that?",
    ),
    3: HintResponse(
        hint="The Illuminated Archive references a famous document signed at Runnymede by King John of England.",
        voice_friendly="King John signed a historic charter in 1215. It is one of the most important legal documents ever written.",
    ),
}

_DEFAULT_HINT = HintResponse(
    hint="Explore the objects around you. Each one holds a piece of knowledge waiting to be discovered.",
    voice_friendly="Look around again. Every object here can teach you something new.",
)


class MockHintProvider(HintProvider):
    async def get_hint(
        self,
        context: dict,
        step: int,
        question: str | None = None,
    ) -> HintResponse:
        return _HINTS.get(step, _DEFAULT_HINT)
